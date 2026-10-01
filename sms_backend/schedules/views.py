"""
ViewSets for schedules app.
"""

from django.conf import settings
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from rest_framework import filters, pagination, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAdmin
from .models import Section, StudentSchedule, TimeSlot
from .scheduler import regenerate_all_schedules
from .serializers import (
    SectionSerializer,
    StudentScheduleSerializer,
    TimeSlotSerializer,
)
from .terms import InvalidTerm, resolve_term, term_options


class SchedulePagination(pagination.PageNumberPagination):
    """Lets clients request a larger page so the weekly grid loads in one call."""

    page_size_query_param = 'page_size'
    max_page_size = 500


class TermOptionsView(viewsets.ViewSet):
    """GET /api/terms/ : the semester and school year options the UI offers."""

    def list(self, request):
        return Response(term_options())


class TimeSlotViewSet(viewsets.ModelViewSet):
    """
    CRUD for reusable time slots.
    Admin-only for writes; all authenticated users can read.
    """

    serializer_class = TimeSlotSerializer

    def get_queryset(self):
        # Chronological Mon..Sun ordering comes from the model Meta.ordering.
        return TimeSlot.objects.all()

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            from rest_framework.permissions import IsAuthenticated
            return [IsAuthenticated()]
        return [IsAdmin()]


class SectionViewSet(viewsets.ModelViewSet):
    """
    CRUD for subject sections.

    A section is what actually meets at a given time, so a subject can run
    several sections concurrently without clashing.
    """

    serializer_class = SectionSerializer
    queryset = Section.objects.select_related('subject', 'instructor').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject']
    search_fields = ['code', 'subject__code', 'subject__name']
    ordering_fields = ['code', 'created_at']
    ordering = ['subject__code', 'code']

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            from rest_framework.permissions import IsAuthenticated
            return [IsAuthenticated()]
        return [IsAdmin()]

    @action(detail=True, methods=['post', 'put'], url_path='students')
    @transaction.atomic
    def set_students(self, request, pk=None):
        """
        POST /api/sections/{id}/students/
        Body: {"student_ids": ["STU-10001"], "remove": false,
               "semester": "1st Sem", "school_year": "2025-2026"}

        Adds students to the section, or drops them with "remove": true, then
        reschedules the section so its students share one class time.
        """
        from students.models import Student

        section = self.get_object()

        # Validate before mutating so a bad term cannot half-apply.
        try:
            semester, school_year = resolve_term(request.data)
        except InvalidTerm as exc:
            return Response({exc.field: [exc.message]}, status=400)

        raw_ids = request.data.get('student_ids', [])
        if hasattr(request.data, 'getlist'):
            raw_ids = request.data.getlist('student_ids')
        if not isinstance(raw_ids, (list, tuple)):
            raw_ids = [raw_ids]
        raw_ids = [str(i).strip() for i in raw_ids if str(i).strip()]

        students = list(Student.objects.filter(id__in=raw_ids))
        found = {s.id for s in students}
        missing = [i for i in raw_ids if i not in found]

        remove = str(request.data.get('remove', '')).lower() in ('1', 'true', 'yes')
        if remove:
            section.students.remove(*students)
        else:
            section.students.add(*students)

        from .scheduler import schedule_section

        slot = schedule_section(section, semester=semester, school_year=school_year)

        return Response({
            'detail': (
                f'Removed {len(students)} student(s) from {section}.'
                if remove
                else f'Enrolled {len(students)} student(s) in {section}.'
            ),
            'added': [] if remove else [s.id for s in students],
            'removed': [s.id for s in students] if remove else [],
            'not_found': missing,
            'enrolled_count': section.students.count(),
            'schedule': {
                'day': slot.day if slot else None,
                'start_time': str(slot.start_time) if slot else None,
                'end_time': str(slot.end_time) if slot else None,
                'term': f'{semester} {school_year}'.strip(),
            },
        })

    def perform_create(self, serializer):
        # A brand new section is not yet scheduled.
        serializer.save()
        from .scheduler import schedule_section

        try:
            semester, school_year = resolve_term({})
        except InvalidTerm:
            return
        schedule_section(serializer.instance, semester=semester, school_year=school_year)


class StudentScheduleViewSet(viewsets.ModelViewSet):
    """
    CRUD for student schedule entries.
    Read for all authenticated users (students see only their own); admin writes.
    """

    serializer_class = StudentScheduleSerializer
    pagination_class = SchedulePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'subject', 'section', 'semester', 'school_year', 'time_slot']
    search_fields = ['student__name', 'student__id', 'subject__code', 'subject__name', 'section__code']
    ordering_fields = ['created_at', 'updated_at', 'time_slot__start_time']
    ordering = None

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return StudentSchedule.objects.none()

        base = StudentSchedule.objects.select_related(
            'student', 'student__user', 'subject', 'section', 'time_slot'
        )
        # Admin and teacher can see all; students only their own
        if user.role == 'student':
            base = base.filter(student__user=user)
        elif user.role not in ['admin', 'teacher'] and not user.is_superuser:
            return StudentSchedule.objects.none()

        return base

    def create(self, request, *args, **kwargs):
        """
        POST /api/schedules/

        A student holds at most one entry per subject per term, so posting a
        subject they are already scheduled in moves that class to the new time
        instead of failing the unique-together check.
        """
        data = request.data
        try:
            semester, school_year = resolve_term(data)
        except InvalidTerm as exc:
            return Response({exc.field: [exc.message]}, status=status.HTTP_400_BAD_REQUEST)

        existing = None
        if data.get('student') and data.get('subject'):
            existing = StudentSchedule.objects.filter(
                student_id=data['student'],
                subject_id=data['subject'],
                semester=semester,
                school_year=school_year,
            ).first()

        if existing is not None:
            serializer = self.get_serializer(existing, data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {
                    **serializer.data,
                    'detail': 'Student already has this subject this term; its time was updated.',
                    'moved': True,
                },
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_all(self, request):
        """
        POST /api/schedules/generate/
        Body: {"student_ids": ["STU-10001"], "semester": "1st Sem", "school_year": "2025-2026"}
        Regenerate schedules. Omit student_ids to rebuild every section and
        subject for the term.
        """
        try:
            semester, school_year = resolve_term(request.data)
        except InvalidTerm as exc:
            return Response({exc.field: [exc.message]}, status=400)

        student_ids = request.data.get('student_ids', [])
        results = regenerate_all_schedules(
            semester=semester,
            school_year=school_year,
            student_ids=student_ids or None,
        )

        scheduled = 0
        payload = []
        for r in results:
            if r['time_slot'] is not None:
                scheduled += r['student_count']
            payload.append({
                'subject': r['subject'].code,
                'section': r.get('section'),
                'day': r['time_slot'].day if r['time_slot'] else None,
                'start_time': str(r['time_slot'].start_time) if r['time_slot'] else None,
                'end_time': str(r['time_slot'].end_time) if r['time_slot'] else None,
                'student_count': r['student_count'],
                'scheduled': r['time_slot'] is not None,
            })

        return Response({
            'detail': 'Schedules generated.',
            'term': f'{semester} {school_year}'.strip(),
            'subjects_scheduled': sum(1 for r in results if r['time_slot'] is not None),
            'classes_scheduled': scheduled,
            'results': payload,
        })
