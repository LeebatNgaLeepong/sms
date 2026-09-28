"""
ViewSets for students app.
"""

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import StudentPermission
from .models import Student
from .serializers import StudentSerializer


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Student management:
    - GET /api/students/ : List students (Admin/Teacher view all; Student views only themselves)
    - POST /api/students/ : Create a student record (Admin only)
    - GET /api/students/{id}/ : Retrieve a student record (Admin, Teacher, or the Student themselves)
    - PUT/PATCH/DELETE /api/students/{id}/ : Update or remove student (Admin only)
    - GET /api/students/{id}/grades/ : View all grades + computed GPA for this student
    """

    serializer_class = StudentSerializer
    permission_classes = [StudentPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'program', 'email', 'id']
    filterset_fields = ['program', 'year_level']
    ordering_fields = ['id', 'name', 'program', 'year_level', 'created_at']
    ordering = ['id']

    def get_queryset(self):
        user = self.request.user
        base_qs = Student.objects.select_related('user').all()

        if not user.is_authenticated:
            return base_qs.none()

        # Admin and Teacher can access all student profiles
        if user.role in ['admin', 'teacher'] or user.is_superuser:
            return base_qs

        # Students can only access their own student profile
        if user.role == 'student':
            return base_qs.filter(user=user)

        return base_qs.none()

    @action(detail=True, methods=['get'], url_path='grades')
    def grades(self, request, pk=None):
        """
        GET /api/students/{id}/grades/
        Returns all grades, subject details, and the computed GPA for the student.
        Enforces object-level permission check (only Admin, Teacher, or the Student themselves).
        """
        student = self.get_object()
        grades_qs = student.grades.select_related('subject', 'recorded_by').order_by('subject__code')

        grades_data = []
        for g in grades_qs:
            grades_data.append({
                'id': g.id,
                'subject': {
                    'id': g.subject.id,
                    'code': g.subject.code,
                    'name': g.subject.name,
                    'units': g.subject.units,
                },
                'score': str(g.score),
                'letter': g.letter,
                'grade_points': str(g.grade_points),
                'recorded_by': g.recorded_by.username if g.recorded_by else None,
                'created_at': g.created_at,
                'updated_at': g.updated_at,
            })

        response_payload = {
            'student_id': student.id,
            'student_name': student.name,
            'email': student.email,
            'program': student.program,
            'year_level': student.year_level,
            'gpa': student.gpa,
            'total_grades': len(grades_data),
            'grades': grades_data,
        }

        return Response(response_payload, status=status.HTTP_200_OK)
