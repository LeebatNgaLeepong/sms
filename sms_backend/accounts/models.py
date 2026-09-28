"""
Accounts models for College Student Management System.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based authorization.
    Roles:
      - Admin: full CRUD on students, subjects, grades, users.
      - Teacher: view all students/subjects; create/edit grades for assigned subjects.
      - Student: read-only access to own profile and own grades.
    """

    ROLE_ADMIN = 'admin'
    ROLE_TEACHER = 'teacher'
    ROLE_STUDENT = 'student'

    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin'),
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_STUDENT, 'Student'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        help_text="Designates the role and permissions for this user.",
    )

    @property
    def is_admin_role(self) -> bool:
        """Return True if user is an admin or superuser."""
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_teacher_role(self) -> bool:
        """Return True if user is a teacher."""
        return self.role == self.ROLE_TEACHER

    @property
    def is_student_role(self) -> bool:
        """Return True if user is a student."""
        return self.role == self.ROLE_STUDENT

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"
