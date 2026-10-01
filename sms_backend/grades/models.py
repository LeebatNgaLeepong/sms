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
  INC = Incomplete (no score yet, assigned by staff, excluded from averages)
  5.00 = below 75 (Fail)
"""

from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Marker for a subject that has not been completed yet. It is not a grade on the
# 1.00-5.00 scale, so it carries no grade points and is left out of GPA and GWA.
GRADE_INC = 'INC'


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
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('0.00'), message="Score cannot be below 0."),
            MaxValueValidator(Decimal('100.00'), message="Score cannot exceed 100."),
        ],
        help_text="Numerical score between 0.00 and 100.00. Leave empty for INC.",
    )
    is_incomplete = models.BooleanField(
        default=False,
        help_text="Subject not completed yet. Recorded as INC with no grade points.",
    )
    letter = models.CharField(
        max_length=5,
        editable=False,
        help_text="Auto-computed grade (1.00, 1.25, ..., 5.00, or INC).",
    )
    grade_points = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        editable=False,
        null=True,
        blank=True,
        help_text="Auto-computed grade points (1.00=best, 3.00=pass, 5.00=fail). Empty for INC.",
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

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.is_incomplete:
            if self.score is not None:
                raise ValidationError({
                    'score': 'An INC grade has no score. Clear the score first.',
                })
        elif self.score is None:
            raise ValidationError({
                'score': 'Enter a score, or mark the grade as INC.',
            })

    def save(self, *args, **kwargs):
        # Always derive letter and grade points server-side from score.
        if self.is_incomplete:
            self.letter = GRADE_INC
            self.grade_points = None
        else:
            letter, points = compute_grade_details(self.score)
            self.letter = letter
            self.grade_points = points
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        if self.is_incomplete:
            return f"{self.student.id} - {self.subject.code}: INC"
        return f"{self.student.id} - {self.subject.code}: {self.score} ({self.letter})"