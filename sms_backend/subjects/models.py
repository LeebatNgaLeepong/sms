"""
Subjects models for College Student Management System.
"""

from django.conf import settings
from django.db import models


class Subject(models.Model):
    """
    Subject model representing college courses/subjects.
    Instructor is constrained to users with role='teacher'.
    """

    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique course code (e.g., CS101, MATH201).",
    )
    name = models.CharField(
        max_length=255,
        help_text="Full course title (e.g., Introduction to Programming).",
    )
    units = models.PositiveSmallIntegerField(
        help_text="Number of credit units (e.g., 3).",
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instructed_subjects',
        limit_choices_to={'role': 'teacher'},
        help_text="Assigned faculty instructor for this subject.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
