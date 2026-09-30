"""
ViewSets for schedules app.
"""

from django.db.models import Case, IntegerField, Value, When
from rest_framework import filters, pagination, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAdmin
from .models import StudentSchedule, TimeSlot
from .scheduler import DAY_ORDER, regenerate_student_schedule
from .serializers import StudentScheduleSerializer, TimeSlotSerializer


def with_day_order(queryset, day_field='time_slot__day'):
    """Annotate a chronological weekday rank so results order Mon..Sun, not alphabetically."""
    whens = [
        When(**{day_field: day}, then=Value(index))
        for index, day in enumerate(DAY_ORDER)
    ]
    return queryset.annotate(
        day_order=Case(*whens, default=Value(len(DAY_ORDER)), output_field=IntegerField())
    )


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
        return with_day_order(TimeSlot.objects.all(), day_field='day').order_by('day_order', 'start_time')

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
    ordering_fields = ['created_at', 'updated_at', 'day_order', 'time_slot__start_time']
    ordering = ['student__id', 'day_order', 'time_slot__start_time']

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

        return with_day_order(base).order_by('student__id', 'day_order', 'time_slot__start_time')

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_all(self, request):
        """
        POST /api/schedules/generate/
        Body: {"student_ids": [1, 2, 3], "semester": "...", "school_year": "..."}
        Regenerate schedules for the given students.
        """
        from students.models import Student

        student_ids = request.data.get('student_ids', [])
        semester = request.data.get('semester', '')
        school_year = request.data.get('school_year', '')

        students = Student.objects.filter(id__in=student_ids)
        results = []
        for student in students:
            result = regenerate_student_schedule(
                student, semester=semester, school_year=school_year
            )
            results.append({
                'student_id': student.id,
                'student_name': student.name,
                'schedules': [
                    {
                        'subject': r['subject'].code,
                        'time_slot': str(r['time_slot']) if r['time_slot'] else None,
                        'created': r['created'],
                    }
                    for r in result
                ],
            })
        return Response({'detail': 'Schedules generated.', 'results': results})