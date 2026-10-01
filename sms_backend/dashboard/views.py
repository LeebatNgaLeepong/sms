"""
Dashboard views for College Student Management System.
Provides summary metrics including counts, system-wide average GPA, and grade distributions.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from grades.models import Grade
from students.models import Student
from subjects.models import Subject

User = get_user_model()


class DashboardSummaryView(APIView):
    """
    GET /api/dashboard/summary/
    Returns institutional-level metrics:
      - total_students: Total number of registered students
      - total_subjects: Total number of academic courses/subjects
      - total_grades: Total number of submitted grades
      - average_gpa: Average GPA across all students with recorded grades (rounded to 2 decimals)
      - grade_distribution: Breakdown of letter grades (A, B, C, D, F)
      - total_teachers: Total number of faculty members
      - passing_rate: Percentage of passing grades (A, B, C, D)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        total_students = Student.objects.count()
        total_subjects = Subject.objects.count()
        total_grades = Grade.objects.count()
        total_teachers = User.objects.filter(role='teacher').count()

        # Average GPA (simple) and GWA (weighted by units) across graded students
        students_with_grades = list(
            Student.objects.filter(grades__isnull=False).distinct()
        )
        if students_with_grades:
            average_gpa = round(sum(s.gpa for s in students_with_grades) / len(students_with_grades), 2)
            average_gwa = round(sum(s.gwa for s in students_with_grades) / len(students_with_grades), 2)
        else:
            average_gpa = 0.00
            average_gwa = 0.00

        # Grade distribution breakdown (University of Antique scale)
        distribution_counts = (
            Grade.objects.values('letter').annotate(count=Count('id')).order_by('letter')
        )
        distribution_dict = {
            '1.00': 0, '1.25': 0, '1.50': 0, '1.75': 0,
            '2.00': 0, '2.25': 0, '2.50': 0, '2.75': 0,
            '3.00': 0, 'INC': 0, '5.00': 0,
        }
        for item in distribution_counts:
            letter = item['letter']
            if letter in distribution_dict:
                distribution_dict[letter] = item['count']

        # Passing grades are 1.00-3.00; 5.00 is fail. Counted from grade_points
        # rather than the letter dict so an unrecognised letter cannot skew it.
        passing_grades_count = Grade.objects.filter(
            grade_points__lte=Decimal('3.00')
        ).count()
        passing_rate = (
            round((passing_grades_count / total_grades) * 100, 1)
            if total_grades > 0
            else 0.0
        )

        return Response({
            'total_students': total_students,
            'total_subjects': total_subjects,
            'total_grades': total_grades,
            'average_gpa': average_gpa,
            'average_gwa': average_gwa,
            'total_teachers': total_teachers,
            'grade_distribution': distribution_dict,
            'passing_rate': passing_rate,
        })
