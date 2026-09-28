"""
Tests for subjects app.
Verifies CRUD access and admin-only write permissions.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from subjects.models import Subject

User = get_user_model()


class SubjectAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_sub", email="admin_sub@test.com", password="pw", role=User.ROLE_ADMIN
        )
        self.teacher = User.objects.create_user(
            username="teacher_sub", email="teacher_sub@test.com", password="pw", role=User.ROLE_TEACHER
        )
        self.student = User.objects.create_user(
            username="student_sub", email="student_sub@test.com", password="pw", role=User.ROLE_STUDENT
        )
        self.subject = Subject.objects.create(
            code="MATH101",
            name="College Algebra",
            units=3,
            instructor=self.teacher,
        )

    def test_authenticated_can_list_subjects(self):
        self.client.force_authenticate(user=self.student)
        res = self.client.get(reverse('subject-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_create_subject(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(reverse('subject-list'), {
            'code': 'CS301',
            'name': 'Operating Systems',
            'units': 4,
            'instructor': self.teacher.id,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['code'], 'CS301')

    def test_teacher_cannot_create_subject(self):
        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(reverse('subject-list'), {
            'code': 'BIO101',
            'name': 'Biology',
            'units': 3,
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
