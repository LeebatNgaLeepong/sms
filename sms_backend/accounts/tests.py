"""
Unit and integration tests for accounts app.
Tests custom User model roles and JWT authentication endpoints.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AccountsAuthTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_user",
            email="admin@test.com",
            password="securepassword123",
            role=User.ROLE_ADMIN,
        )
        self.teacher = User.objects.create_user(
            username="teacher_user",
            email="teacher@test.com",
            password="securepassword123",
            role=User.ROLE_TEACHER,
        )
        self.student_user = User.objects.create_user(
            username="student_user",
            email="student@test.com",
            password="securepassword123",
            role=User.ROLE_STUDENT,
        )

    def test_user_roles(self):
        self.assertTrue(self.admin.is_admin_role)
        self.assertTrue(self.teacher.is_teacher_role)
        self.assertTrue(self.student_user.is_student_role)

    def test_jwt_login_success(self):
        url = reverse('auth_login')
        response = self.client.post(url, {
            'username': 'admin_user',
            'password': 'securepassword123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['role'], 'admin')

    def test_jwt_refresh(self):
        login_res = self.client.post(reverse('auth_login'), {
            'username': 'teacher_user',
            'password': 'securepassword123',
        })
        refresh_token = login_res.data['refresh']

        refresh_res = self.client.post(reverse('auth_refresh'), {
            'refresh': refresh_token,
        })
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)

    def test_jwt_logout_blacklists_token(self):
        login_res = self.client.post(reverse('auth_login'), {
            'username': 'student_user',
            'password': 'securepassword123',
        })
        refresh_token = login_res.data['refresh']
        access_token = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_res = self.client.post(reverse('auth_logout'), {'refresh': refresh_token})
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        # Refreshing with the blacklisted token must fail
        retry_res = self.client.post(reverse('auth_refresh'), {'refresh': refresh_token})
        self.assertEqual(retry_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint(self):
        login_res = self.client.post(reverse('auth_login'), {
            'username': 'teacher_user',
            'password': 'securepassword123',
        })
        token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        me_res = self.client.get(reverse('auth_me'))
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data['username'], 'teacher_user')
        self.assertEqual(me_res.data['role'], 'teacher')
