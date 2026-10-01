"""
Tests for dashboard app.
Verifies summary metrics calculation.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from grades.models import Grade
from students.models import Student
from subjects.models import Subject

User = get_user_model()


class DashboardSummaryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin_dash", email="admin_dash@test.com", password="pw", role=User.ROLE_ADMIN
        )
        self.teacher = User.objects.create_user(
            username="teacher_dash", email="teacher_dash@test.com", password="pw", role=User.ROLE_TEACHER
        )

        self.student1 = Student.objects.create(
            name="Alice Dash", email="alice_dash@test.com", program="BS CS", year_level="1st"
        )
        self.student2 = Student.objects.create(
            name="Bob Dash", email="bob_dash@test.com", program="BS CS", year_level="1st"
        )

        self.subject1 = Subject.objects.create(code="CS101", name="CS 1", units=3, instructor=self.teacher)
        self.subject2 = Subject.objects.create(code="CS102", name="CS 2", units=3, instructor=self.teacher)

# Alice: 95 (1.25), GPA = 1.25
        Grade.objects.create(student=self.student1, subject=self.subject1, score=Decimal('95.00'))
        # Bob: 85 (2.25), GPA = 2.25
        Grade.objects.create(student=self.student2, subject=self.subject2, score=Decimal('85.00'))
        # Expected Average GPA across students = (1.25 + 2.25) / 2 = 1.75

    def test_unauthenticated_forbidden(self):
        res = self.client.get(reverse('dashboard_summary'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_summary_metrics(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(reverse('dashboard_summary'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_students'], 2)
        self.assertEqual(res.data['total_subjects'], 2)
        self.assertEqual(res.data['total_grades'], 2)
        self.assertEqual(res.data['average_gpa'], 1.75)
        self.assertIn('grade_distribution', res.data)
        self.assertEqual(res.data['grade_distribution']['1.25'], 1)
        self.assertEqual(res.data['grade_distribution']['2.25'], 1)

    def test_distribution_includes_a_manual_grade_outside_the_scale(self):
        """A manually recorded grade must not vanish from the chart."""
        Grade.objects.create(
            student=self.student1,
            subject=self.subject2,
            score=None,
            manual_points=Decimal('4.00'),
        )
        self.client.force_authenticate(user=self.user)
        res = self.client.get(reverse('dashboard_summary'))
        self.assertIn('4.00', res.data['grade_distribution'])
        self.assertEqual(res.data['grade_distribution']['4.00'], 1)

    def test_passing_rate_counts_passes_only(self):
        """A 5.00 (fail) must drag the passing rate down but not zero it out."""
        Grade.objects.create(
            student=self.student1,
            subject=self.subject2,
            score=Decimal('60.00'),
        )
        # 1.25, 2.25, 5.00 -> 2 of 3 pass
        self.client.force_authenticate(user=self.user)
        res = self.client.get(reverse('dashboard_summary'))
        self.assertEqual(res.data['total_grades'], 3)
        self.assertEqual(res.data['grade_distribution']['5.00'], 1)
        self.assertEqual(res.data['passing_rate'], 66.7)
