"""
ViewSets for schedules app.
"""

from django.conf import settings
from rest_framework import filters, pagination, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAdmin
from .models import StudentSchedule, TimeSlot
from .scheduler import regenerate_all_schedules
from .serializers import StudentScheduleSerializer, TimeSlotSerializer


class SchedulePagination(pagination.PageNumberPagination):
    """Lets clients request a larger page so the weekly grid loads in one call."""

    page_size_query_param = 'page_size'
    max_page_size = 500


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


class StudentScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student class schedules.

    - GET /api/schedules/ : List schedules (filtered by ?student=&semester=)
    - POST /api/schedules/ : Create a schedule entry (Admin only)
    - GET /api/schedules/{id}/ : Retrieve schedule details
    - PUT/PATCH/DELETE /api/schedules/{id}/ : Update or remove schedule (Admin only)
    - GET /api/students/{id}/schedules/ : View all schedules for a student
    - POST /api/students/{id}/schedules/generate/ : Auto-generate schedules for enrolled subjects
    """

    serializer_class = StudentScheduleSerializer
    pagination_class = SchedulePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'subject', 'semester', 'school_year', 'time_slot']
    search_fields = ['student__name', 'subject__code', 'subject__name']
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
            'student', 'student__user', 'subject', 'time_slot'
        )
        # Admin and teacher can see all; students only their own
        if user.role == 'student':
            base = base.filter(student__user=user)
        elif user.role not in ['admin', 'teacher'] and not user.is_superuser:
            return StudentSchedule.objects.none()

        return base

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_all(self, request):
        """
        POST /api/schedules/generate/
        Body: {"student_ids": ["STU-10001"], "semester": "...", "school_year": "..."}
        Regenerate schedules. Omit student_ids to rebuild every subject for the term.
        """
        student_ids = request.data.get('student_ids', [])
        semester = request.data.get('semester') or settings.CURRENT_SEMESTER
        school_year = request.data.get('school_year') or settings.CURRENT_SCHOOL_YEAR

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
                'subject_name': r['subject'].name,
                'day': r['time_slot'].day if r['time_slot'] else None,
                'start_time': str(r['time_slot'].start_time) if r['time_slot'] else None,
                'end_time': str(r['time_slot'].end_time) if r['time_slot'] else None,
                'student_count': r['student_count'],
                'scheduled': r['time_slot'] is not None,
            })

        return Response({
            'detail': 'Schedules generated.',
            'subjects_scheduled': sum(1 for r in results if r['time_slot'] is not None),
            'classes_scheduled': scheduled,
            'results': payload,
        })