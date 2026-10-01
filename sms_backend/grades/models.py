"""
Grades models for College Student Management System.
Implements University of Antique grading scale (Philippine 1.0-5.0 system).

The bands live in settings.GRADE_SCALE so they can be changed without touching
code. See that setting for the default bands and how to add one.
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
    Derive grade code and grade points from a score using settings.GRADE_SCALE.

    Bands are checked highest first; the band with ``min: None`` is the
    catch-all, so a score below the passing band lands on the failing grade
    rather than being left ungraded.
    """
    score_val = Decimal(str(score))
    for band in settings.GRADE_SCALE:
        minimum = band.get('min')
        if minimum is None or score_val >= Decimal(str(minimum)):
            return str(band['letter']), Decimal(str(band['points']))
    # Unreachable while the scale ends with a catch-all band.
    last = settings.GRADE_SCALE[-1]
    return str(last['letter']), Decimal(str(last['points']))


def letter_for_points(points: Decimal | float) -> str:
    """The grade code recorded for a given grade points value."""
    points_val = Decimal(str(points))
    for band in settings.GRADE_SCALE:
        if Decimal(str(band['points'])) == points_val:
            return str(band['letter'])
    return f'{points_val:.2f}'


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
    manual_points = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=(
            "Grade points entered directly by staff, overriding the score bands. "
            "Use this to record a grade the scale has no band for."
        ),
    )
    remark = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional note, e.g. a reason for a manual grade.",
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
                'score': 'Enter a score, set grade points manually, or mark it as INC.',
            })

    def save(self, *args, **kwargs):
        # Always derive letter and grade points server-side, never from input.
        if self.is_incomplete:
            self.letter = GRADE_INC
            self.grade_points = None
        elif self.manual_points is not None:
            # Staff set the grade points directly; the score bands are bypassed.
            self.grade_points = self.manual_points
            self.letter = letter_for_points(self.manual_points)
        else:
            letter, points = compute_grade_details(self.score)
            self.letter = letter
            self.grade_points = points
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        if self.is_incomplete:
            return f"{self.student.id} - {self.subject.code}: INC"
        return f"{self.student.id} - {self.subject.code}: {self.letter}"