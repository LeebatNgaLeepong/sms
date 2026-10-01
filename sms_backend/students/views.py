"""
ViewSets for students app.
"""

import logging

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import StudentPermission
from schedules.terms import InvalidTerm, resolve_term
from subjects.models import Subject
from .models import Student
from .serializers import StudentSerializer

logger = logging.getLogger(__name__)


class ScheduleGenerationError(Exception):
    """Raised internally so a failed run rolls back the whole enrollment."""


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
        # grades_count is annotated so listing students does not need one query
        # per student; incomplete_count comes from the same grade rows.
        base_qs = (
            Student.objects.select_related('user')
            .prefetch_related('enrolled_subjects')
            .annotate(
                grades_count=Count('grades'),
                # Named inc_count, not incomplete_count: the model has a read-only
                # property of that name and an annotation would collide with it.
                inc_count=Count(
                    'grades',
                    filter=Q(grades__is_incomplete=True),
                ),
            )
            .all()
        )

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
                'score': str(g.score) if g.score is not None else None,
                'letter': g.letter,
                'grade_points': str(g.grade_points) if g.grade_points is not None else None,
                'is_incomplete': g.is_incomplete,
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
            'gwa': student.gwa,
            'units_earned': student.units_earned,
            'incomplete_count': student.incomplete_count,
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
            return Response(
                {'detail': 'Only admins can modify enrollments.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            return self._enroll(request)
        except ScheduleGenerationError:
            return Response(
                {'detail': 'Enrollment could not be scheduled. No changes were saved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _enroll(self, request):
        student = self.get_object()
        # QueryDict (multipart/form-data) needs getlist() to keep every repeated id.
        if hasattr(request.data, 'getlist'):
            subject_ids = request.data.getlist('subject_ids')
        else:
            subject_ids = request.data.get('subject_ids', [])
        if not isinstance(subject_ids, (list, tuple)):
            subject_ids = [subject_ids]
        # Ids arrive as strings over form-data and JSON alike, so normalise them
        # before they reach the database and fail on a non-numeric value.
        subject_ids = [str(i).strip() for i in subject_ids if str(i).strip()]
        invalid = [i for i in subject_ids if not i.isdigit()]
        if invalid:
            return Response(
                {'detail': f"Invalid subject_ids: {', '.join(invalid)}. Expected numbers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            semester, school_year = resolve_term(request.data)
        except InvalidTerm as exc:
            return Response({exc.field: [exc.message]}, status=400)

        subjects = list(Subject.objects.filter(id__in=subject_ids))
        found = {str(s.id) for s in subjects}
        missing = [i for i in subject_ids if i not in found]

        # Enrollment and its generated schedules are one unit of work: a
        # scheduler failure must not leave the student with a different set of
        # subjects than the schedules the response reports.
        with transaction.atomic():
            student.enrolled_subjects.set(subjects)

            from schedules.scheduler import regenerate_student_schedule
            try:
                schedule_result = regenerate_student_schedule(
                    student, semester=semester, school_year=school_year
                )
            except Exception:
                logger.exception('Schedule generation failed for student %s', student.id)
                # Returning here would let the atomic block commit, so the
                # failure has to travel out as an exception to roll it back.
                raise ScheduleGenerationError

        scheduled_count = sum(1 for r in schedule_result if r['time_slot'] is not None)
        return Response({
            'student_id': student.id,
            'enrolled_count': len(subjects),
            'scheduled_count': scheduled_count,
            'not_found': missing,
            'detail': 'Enrollment updated successfully. Schedules auto-generated.',
        })
