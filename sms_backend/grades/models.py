"""
Grades models for College Student Management System.
Includes automatic computation of letter grades and grade points from numerical scores.
"""

from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def compute_grade_details(score: Decimal | float) -> tuple[str, Decimal]:
    """
    Derive letter grade and grade points server-side from score.
      90–100   = A (4.00)
      80–89.99 = B (3.00)
      70–79.99 = C (2.00)
      60–69.99 = D (1.00)
      below 60 = F (0.00)
    """
    score_val = Decimal(str(score))
    if score_val >= Decimal('90.00'):
        return 'A', Decimal('4.00')
    elif score_val >= Decimal('80.00'):
        return 'B', Decimal('3.00')
    elif score_val >= Decimal('70.00'):
        return 'C', Decimal('2.00')
    elif score_val >= Decimal('60.00'):
        return 'D', Decimal('1.00')
    else:
        return 'F', Decimal('0.00')


class Grade(models.Model):
    """
    Grade model associating a Student and Subject with a validated score,
    auto-computed letter grade, and grade points.
    """

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='grades',
        help_text="The student receiving this grade.",
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='grades',
        help_text="The subject for which this grade is recorded.",
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00'), message="Score cannot be below 0."),
            MaxValueValidator(Decimal('100.00'), message="Score cannot exceed 100."),
        ],
        help_text="Numerical score between 0.00 and 100.00.",
    )
    letter = models.CharField(
        max_length=2,
        editable=False,
        help_text="Auto-computed letter grade (A, B, C, D, F).",
    )
    grade_points = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        editable=False,
        help_text="Auto-computed grade points (4.00, 3.00, 2.00, 1.00, 0.00).",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_grades',
        help_text="User (Admin or assigned Teacher) who recorded this grade.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('student', 'subject')

    def save(self, *args, **kwargs):
        # Always derive letter and grade points server-side from score
        letter, points = compute_grade_details(self.score)
        self.letter = letter
        self.grade_points = points
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.student.id} - {self.subject.code}: {self.score} ({self.letter})"
