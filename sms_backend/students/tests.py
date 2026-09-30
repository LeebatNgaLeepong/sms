"""
Tests for students app.
Verifies auto ID generation, GPA computation, and role-based permissions.
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


class StudentAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin1", email="admin1@test.com", password="pw", role=User.ROLE_ADMIN
        )
        self.teacher = User.objects.create_user(
            username="teacher1", email="teacher1@test.com", password="pw", role=User.ROLE_TEACHER
        )
        self.student_user_1 = User.objects.create_user(
            username="stu1", email="stu1@test.com", password="pw", role=User.ROLE_STUDENT
        )
        self.student_user_2 = User.objects.create_user(
            username="stu2", email="stu2@test.com", password="pw", role=User.ROLE_STUDENT
        )

        self.student1 = Student.objects.create(
            user=self.student_user_1,
            name="Student One",
            email="stu1@test.com",
            program="BS CS",
            year_level="1st Year",
        )
        self.student2 = Student.objects.create(
            user=self.student_user_2,
            name="Student Two",
            email="stu2@test.com",
            program="BS IT",
            year_level="2nd Year",
        )

        self.subject = Subject.objects.create(
            code="CS101",
            name="Intro CS",
            units=3,
            instructor=self.teacher,
        )

    def test_student_auto_id_format(self):
        self.assertTrue(self.student1.id.startswith('STU-'))

    def test_admin_can_create_student(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-list')
        data = {
            'name': 'New Student',
            'email': 'newstu@test.com',
            'program': 'BS Math',
            'year_level': '1st Year',
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['id'].startswith('STU-'))

    def test_teacher_cannot_create_student(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse('student-list')
        data = {'name': 'Teacher Student', 'email': 'tstu@test.com', 'program': 'BS', 'year_level': '1st'}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_only_view_own_profile(self):
        self.client.force_authenticate(user=self.student_user_1)

        # Listing only returns student 1
        res = self.client.get(reverse('student-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Results inside pagination
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.student1.id)

        # Accessing own detail succeeds
        res_own = self.client.get(reverse('student-detail', kwargs={'pk': self.student1.id}))
        self.assertEqual(res_own.status_code, status.HTTP_200_OK)

        # Accessing other student detail is forbidden (403 or 404)
        res_other = self.client.get(reverse('student-detail', kwargs={'pk': self.student2.id}))
        self.assertIn(res_other.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_student_grades_endpoint(self):
        # Create grade for student 1
        Grade.objects.create(
            student=self.student1,
            subject=self.subject,
            score=Decimal('99.00'),
            recorded_by=self.teacher,
        )

        self.client.force_authenticate(user=self.student_user_1)
        url = reverse('student-grades', kwargs={'pk': self.student1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # GPA for 99.00 should be 1.00 on University of Antique scale
        self.assertEqual(res.data['gpa'], 1.0)
        self.assertEqual(len(res.data['grades']), 1)
        self.assertEqual(res.data['grades'][0]['letter'], '1.00')

    def test_gpa_returns_5_when_no_grades(self):
        """Students with no grades should have GPA of 5.00 (fail) on Antique scale."""
        self.assertEqual(self.student2.gpa, 5.00)


class EnrollmentScheduleTests(APITestCase):
    """Enrolling a student should auto-generate a conflict-free schedule."""

    def setUp(self):
        from datetime import time

        from schedules.models import TimeSlot

        self.admin = User.objects.create_user(
            username="admin_enroll", email="admin_enroll@test.com", password="pw", role=User.ROLE_ADMIN
        )
        self.student_user = User.objects.create_user(
            username="stu_enroll", email="stu_enroll@test.com", password="pw", role=User.ROLE_STUDENT
        )
        self.student = Student.objects.create(
            user=self.student_user,
            name="Enroll Student",
            email="stu_enroll@test.com",
            program="BS CS",
            year_level="1st Year",
        )
        self.subject_a = Subject.objects.create(code="CS201", name="Data Structures", units=4)
        self.subject_b = Subject.objects.create(code="MATH201", name="Calculus", units=4)

        # Two non-overlapping slots are enough to schedule both subjects.
        TimeSlot.objects.create(day='Mon', start_time=time(7, 0), duration_hours=2, slot_type='lec')
        TimeSlot.objects.create(day='Mon', start_time=time(9, 0), duration_hours=2, slot_type='lec')

    def test_enroll_auto_generates_schedules(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-enroll', kwargs={'pk': self.student.id})
        res = self.client.post(url, {
            'subject_ids': [self.subject_a.id, self.subject_b.id],
            'semester': '1st Sem',
            'school_year': '2025-2026',
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['enrolled_count'], 2)
        self.assertEqual(res.data['scheduled_count'], 2)

        schedules = self.student.schedules.all()
        self.assertEqual(schedules.count(), 2)
        self.assertEqual({s.time_slot.day for s in schedules}, {'Mon'})

    def test_enroll_accepts_repeated_form_fields(self):
        """Form-encoded requests repeat subject_ids, so every id must be kept."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-enroll', kwargs={'pk': self.student.id})
        res = self.client.post(url, {
            'subject_ids': [self.subject_a.id, self.subject_b.id],
        }, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['enrolled_count'], 2)
        self.assertEqual(self.student.enrolled_subjects.count(), 2)
        self.assertEqual(self.student.schedules.count(), 2)

    def test_enroll_replaces_previous_schedule(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-enroll', kwargs={'pk': self.student.id})

        self.client.post(url, {
            'subject_ids': [self.subject_a.id, self.subject_b.id],
            'semester': '1st Sem',
            'school_year': '2025-2026',
        }, format='json')
        self.assertEqual(self.student.schedules.count(), 2)

        # Re-enrolling with a single subject should not leave stale schedules.
        res = self.client.post(url, {
            'subject_ids': [self.subject_a.id],
            'semester': '1st Sem',
            'school_year': '2025-2026',
        }, format='json')
        self.assertEqual(res.data['scheduled_count'], 1)
        self.assertEqual(self.student.schedules.count(), 1)