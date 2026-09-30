"""
ViewSets for students app.
"""

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import StudentPermission
from subjects.models import Subject
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
    - GET /api/students/{id}/enrolled/ : View subjects this student is enrolled in
    - POST /api/students/{id}/enroll/ : Enroll student in subjects (Admin only)
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
        base_qs = Student.objects.select_related('user').prefetch_related('enrolled_subjects').all()

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

    @action(detail=True, methods=['get'], url_path='enrolled')
    def enrolled(self, request, pk=None):
        """
        GET /api/students/{id}/enrolled/
        Returns subjects the student is currently enrolled in.
        """
        student = self.get_object()
        subjects = student.enrolled_subjects.select_related('instructor').all()
        data = [
            {
                'id': s.id,
                'code': s.code,
                'name': s.name,
                'units': s.units,
                'instructor_name': (
                    f"{s.instructor.first_name} {s.instructor.last_name}".strip()
                    or s.instructor.username
                ) if s.instructor else None,
            }
            for s in subjects
        ]
        return Response({'student_id': student.id, 'enrolled_subjects': data})

    @action(detail=True, methods=['post', 'put'], url_path='enroll')
    def enroll(self, request, pk=None):
        """
        POST/PUT /api/students/{id}/enroll/
        Body: {"subject_ids": [1, 2, 3], "semester": "...", "school_year": "..."}
        Replaces the student's enrolled subjects with the given list.
        Automatically generates conflict-free class schedules for the enrolled subjects.
        Admin-only.
        """
        if request.user.role not in ['admin'] and not request.user.is_superuser:
            return Response({'detail': 'Only admins can modify enrollments.'}, status=403)

        student = self.get_object()
        # QueryDict (multipart/form-data) needs getlist() to keep every repeated id.
        if hasattr(request.data, 'getlist'):
            subject_ids = request.data.getlist('subject_ids')
        else:
            subject_ids = request.data.get('subject_ids', [])
        if not isinstance(subject_ids, (list, tuple)):
            subject_ids = [subject_ids]
        semester = request.data.get('semester') or settings.CURRENT_SEMESTER
        school_year = request.data.get('school_year') or settings.CURRENT_SCHOOL_YEAR

        try:
            subjects = Subject.objects.filter(id__in=subject_ids)
            student.enrolled_subjects.set(subjects)

            # Auto-generate schedules for the enrolled subjects
            from schedules.scheduler import regenerate_student_schedule
            schedule_result = regenerate_student_schedule(
                student, semester=semester, school_year=school_year
            )

            scheduled_count = sum(1 for r in schedule_result if r['time_slot'] is not None)
            return Response({
                'student_id': student.id,
                'enrolled_count': subjects.count(),
                'scheduled_count': scheduled_count,
                'detail': 'Enrollment updated successfully. Schedules auto-generated.',
            })
        except Exception as e:
            return Response({'detail': str(e)}, status=400)
