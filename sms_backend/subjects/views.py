"""
ViewSets for subjects app.
"""

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import SubjectPermission
from .models import Subject
from .serializers import SubjectSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Subject management:
    - GET /api/subjects/ : list all subjects (any authenticated user)
    - POST /api/subjects/ : create a new subject (Admin only)
    - GET /api/subjects/{id}/ : retrieve details of a subject (any authenticated user)
    - PUT/PATCH/DELETE /api/subjects/{id}/ : modify or remove a subject (Admin only)
    - GET /api/subjects/{id}/students/ : list enrolled students
    - POST /api/subjects/{id}/enroll/ : add or remove students in bulk (Admin only)
    """

    queryset = Subject.objects.select_related('instructor').all()
    serializer_class = SubjectSerializer
    permission_classes = [SubjectPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name']
    filterset_fields = ['instructor', 'units']
    ordering_fields = ['code', 'name', 'units', 'created_at']
    ordering = ['code']

    @action(detail=True, methods=['get'], url_path='students')
    def students(self, request, pk=None):
        """GET /api/subjects/{id}/students/ : students enrolled in this subject."""
        subject = self.get_object()
        enrolled = subject.enrolled_students.order_by('id')
        return Response({
            'subject': subject.code,
            'subject_name': subject.name,
            'count': enrolled.count(),
            'students': [
                {
                    'id': s.id,
                    'name': s.name,
                    'program': s.program,
                    'year_level': s.year_level,
                }
                for s in enrolled
            ],
        })

    @action(detail=True, methods=['post', 'put'], url_path='enroll')
    def enroll_students(self, request, pk=None):
        """
        POST /api/subjects/{id}/enroll/
        Body: {"student_ids": ["STU-10001"], "remove": false,
               "semester": "...", "school_year": "..."}

        Adds the listed students to the subject, or with "remove": true drops
        them. The subject is then scheduled once for the whole cohort so every
        student in it shares the same class time.
        """
        if request.user.role != 'admin' and not request.user.is_superuser:
            return Response(
                {'detail': 'Only admins can modify subject enrollment.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        subject = self.get_object()

        from students.models import Student

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
            subject.enrolled_students.remove(*students)
        else:
            subject.enrolled_students.add(*students)

        semester = request.data.get('semester') or settings.CURRENT_SEMESTER
        school_year = request.data.get('school_year') or settings.CURRENT_SCHOOL_YEAR

        # Schedule the subject once for the whole cohort so every student in it
        # is given the same class time.
        from schedules.scheduler import schedule_subject

        slot = schedule_subject(subject, semester=semester, school_year=school_year)
        slot_info = {
            'day': slot.day if slot else None,
            'start_time': str(slot.start_time) if slot else None,
            'end_time': str(slot.end_time) if slot else None,
            'term': f'{semester} {school_year}'.strip(),
        }

        enrolled = subject.enrolled_students.order_by('id')
        return Response({
            'detail': (
                f'Removed {len(students)} student(s) from {subject.code}.'
                if remove
                else f'Enrolled {len(students)} student(s) in {subject.code}.'
            ),
            'added': [] if remove else [s.id for s in students],
            'removed': [s.id for s in students] if remove else [],
            'not_found': missing,
            'enrolled_count': enrolled.count(),
            'schedule': slot_info,
        })
