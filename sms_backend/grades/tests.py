"""
Tests for grades app.
Validates business logic:
- Server-side score -> letter -> grade_points computation
- Score range constraints (0 to 100)
- Teacher course assignment constraint
- Student read-only isolation
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


class GradeLogicAndAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_g", email="admin_g@test.com", password="pw", role=User.ROLE_ADMIN
        )
        self.teacher1 = User.objects.create_user(
            username="teacher_cs", email="teacher_cs@test.com", password="pw", role=User.ROLE_TEACHER
        )
        self.teacher2 = User.objects.create_user(
            username="teacher_math", email="teacher_math@test.com", password="pw", role=User.ROLE_TEACHER
        )
        self.student_user = User.objects.create_user(
            username="student_g", email="student_g@test.com", password="pw", role=User.ROLE_STUDENT
        )
        self.other_student_user = User.objects.create_user(
            username="student_other", email="student_other@test.com", password="pw", role=User.ROLE_STUDENT
        )

        self.student = Student.objects.create(
            user=self.student_user,
            name="Alice Student",
            email="alice_g@test.com",
            program="BS CS",
            year_level="2nd Year",
        )
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            name="Bob Student",
            email="bob_g@test.com",
            program="BS CS",
            year_level="2nd Year",
        )

        self.cs_subject = Subject.objects.create(
            code="CS101",
            name="Intro CS",
            units=3,
            instructor=self.teacher1,
        )
        self.math_subject = Subject.objects.create(
            code="MATH101",
            name="Calculus",
            units=4,
            instructor=self.teacher2,
        )

    def test_score_to_letter_and_points_computation(self):
        # 95 -> A (4.00)
        g1 = Grade.objects.create(
            student=self.student, subject=self.cs_subject, score=Decimal('95.00')
        )
        self.assertEqual(g1.letter, 'A')
        self.assertEqual(g1.grade_points, Decimal('4.00'))

        # 85 -> B (3.00)
        g2 = Grade.objects.create(
            student=self.other_student, subject=self.cs_subject, score=Decimal('85.00')
        )
        self.assertEqual(g2.letter, 'B')
        self.assertEqual(g2.grade_points, Decimal('3.00'))

    def test_server_ignores_client_supplied_letter_and_points(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.cs_subject.id,
            'score': '75.00',
            'letter': 'A',           # Client attempts to cheat
            'grade_points': '4.00',  # Client attempts to cheat
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['letter'], 'C')
        self.assertEqual(Decimal(res.data['grade_points']), Decimal('2.00'))

    def test_score_validation_out_of_range(self):
        self.client.force_authenticate(user=self.admin)
        # Score > 100
        res = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.cs_subject.id,
            'score': '105.00',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Score < 0
        res2 = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.cs_subject.id,
            'score': '-10.00',
        })
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_can_only_grade_assigned_subject(self):
        self.client.force_authenticate(user=self.teacher1)
        # Teacher 1 grades assigned CS subject -> Allowed
        res = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.cs_subject.id,
            'score': '90.00',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Teacher 1 attempts to grade Math subject (taught by teacher 2) -> Forbidden
        res_fail = self.client.post(reverse('grade-list'), {
            'student': self.other_student.id,
            'subject': self.math_subject.id,
            'score': '90.00',
        })
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('subject', res_fail.data)

    def test_student_read_only_isolation(self):
        # Create grade for student 1
        g1 = Grade.objects.create(
            student=self.student, subject=self.cs_subject, score=Decimal('90.00')
        )
        # Create grade for other student
        g2 = Grade.objects.create(
            student=self.other_student, subject=self.cs_subject, score=Decimal('80.00')
        )

        self.client.force_authenticate(user=self.student_user)

        # Student listing grades should only see their own grade
        res = self.client.get(reverse('grade-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], g1.id)

        # Student cannot create a grade
        post_res = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.math_subject.id,
            'score': '95.00',
        })
        self.assertEqual(post_res.status_code, status.HTTP_403_FORBIDDEN)
