"""
ViewSets for grades app.
Supports listing, filtering by student and subject, and strict role permissions.
"""

from rest_framework import filters, viewsets
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import GradePermission
from .models import Grade
from .serializers import GradeSerializer


class GradeFilter(django_filters.FilterSet):
    """
    Custom filter to support filtering grades by:
      - ?student=STU-10001 (student ID)
      - ?subject=1 or ?subject=CS101 (subject ID or course code)
    """

    student = django_filters.CharFilter(field_name='student__id', lookup_expr='iexact')
    subject = django_filters.CharFilter(method='filter_subject')

    class Meta:
        model = Grade
        fields = ['student', 'subject']

    def filter_subject(self, queryset, name, value):
        if value.isdigit():
            return queryset.filter(subject__id=int(value))
        return queryset.filter(subject__code__iexact=value)


class GradeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Grade operations:
    - GET /api/grades/ : List grades (filter by ?student=&subject=)
        - Admin/Teacher: view all matching grades
        - Student: view only their own grades
    - POST /api/grades/ : Create grade (Admin or teacher assigned to the subject)
    - GET /api/grades/{id}/ : Retrieve grade details (Admin, Teacher, or student owner)
    - PUT/PATCH/DELETE /api/grades/{id}/ : Update or delete grade (Admin or assigned teacher)
    """

    serializer_class = GradeSerializer
    permission_classes = [GradePermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = GradeFilter
    ordering_fields = ['score', 'grade_points', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        user = self.request.user
        base_qs = Grade.objects.select_related(
            'student',
            'subject',
            'subject__instructor',
            'recorded_by'
        )

        if not user.is_authenticated:
            return base_qs.none()

        # Admin and Teacher can view all grades
        if user.role in ['admin', 'teacher'] or user.is_superuser:
            return base_qs

        # Students can view ONLY their own grades
        if user.role == 'student':
            return base_qs.filter(student__user=user)

        return base_qs.none()

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(recorded_by=self.request.user)
