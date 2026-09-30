"""
Grades models for College Student Management System.
Implements University of Antique grading scale (Philippine 1.0-5.0 system).

Grading Scale:
  1.00 = 98-100 (Excellent)
  1.25 = 95-97
  1.50 = 92-94
  1.75 = 89-91
  2.00 = 86-88
  2.25 = 83-85
  2.50 = 80-82
  2.75 = 77-79
  3.00 = 75-76 (Passing)
  4.00 = Incomplete (INC)
  5.00 = below 75 (Fail)
"""

from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def compute_grade_details(score: Decimal | float) -> tuple[str, Decimal]:
    """
    Derive University of Antique grade points server-side from score.
    Uses the Philippine 1.0-5.0 grading scale.
    """
    score_val = Decimal(str(score))
    if score_val >= Decimal('98.00'):
        return '1.00', Decimal('1.00')
    elif score_val >= Decimal('95.00'):
        return '1.25', Decimal('1.25')
    elif score_val >= Decimal('92.00'):
        return '1.50', Decimal('1.50')
    elif score_val >= Decimal('89.00'):
        return '1.75', Decimal('1.75')
    elif score_val >= Decimal('86.00'):
        return '2.00', Decimal('2.00')
    elif score_val >= Decimal('83.00'):
        return '2.25', Decimal('2.25')
    elif score_val >= Decimal('80.00'):
        return '2.50', Decimal('2.50')
    elif score_val >= Decimal('77.00'):
        return '2.75', Decimal('2.75')
    elif score_val >= Decimal('75.00'):
        return '3.00', Decimal('3.00')
    else:
        return '5.00', Decimal('5.00')


class Grade(models.Model):
    """
    Grade model associating a Student and Subject with a validated score,
    auto-computed University of Antique grade points.
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
        max_length=5,
        editable=False,
        help_text="Auto-computed University of Antique grade (1.00, 1.25, ..., 5.00).",
    )
    grade_points = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        editable=False,
        help_text="Auto-computed grade points (1.00=best, 3.00=pass, 4.00=incomplete, 5.00=fail).",
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