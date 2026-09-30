"""
Schedule models for College Student Management System.
Handles class schedules for students with automatic conflict-free generation.

Features:
- Time slots from 7:00 AM to 8:00 PM, Monday through Sunday
- Adjustable start and end times per subject session
- Lab or Lecture type designation
- Automatic conflict-free schedule generation
"""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, IntegerField, Value, When

# Chronological weekday order. Ordering by the stored day code directly would
# sort alphabetically (Fri, Mon, Sat, Sun, Thu, Tue, Wed), so the rank is
# applied as a database expression in Meta.ordering.
DAY_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def day_rank(day_field='day'):
    """Return a Case expression ranking a day code chronologically (Mon=0..Sun=6)."""
    return Case(
        *[When(**{day_field: day}, then=Value(index)) for index, day in enumerate(DAY_ORDER)],
        default=Value(len(DAY_ORDER)),
        output_field=IntegerField(),
    )


class TimeSlot(models.Model):
    """
    Represents a reusable time slot in the weekly schedule.
    Each time slot has a start time, an end time, and a type (Lab or Lecture).
    The end time is set directly; duration_hours is derived from the two times.
    """

    DAY_CHOICES = tuple((code, full) for code, full in [
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
    ])

    SLOT_TYPE_CHOICES = (
        ('lec', 'Lecture'),
        ('lab', 'Laboratory'),
    )

    day = models.CharField(
        max_length=3,
        choices=DAY_CHOICES,
        help_text="Day of the week.",
    )
    start_time = models.TimeField(
        help_text="Start time of the slot (e.g., 07:00).",
    )
    end_time = models.TimeField(
        help_text="End time of the slot (e.g., 09:00). Must be after the start time.",
    )
    duration_hours = models.PositiveSmallIntegerField(
        default=2,
        editable=False,
        help_text="Derived from start_time and end_time.",
    )
    slot_type = models.CharField(
        max_length=3,
        choices=SLOT_TYPE_CHOICES,
        default='lec',
        help_text="Type of class: Lecture or Laboratory.",
    )
    label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional label (e.g., 'Period 1').",
    )

    class Meta:
        ordering = [day_rank(), 'start_time']
        constraints = [
            # A timetable cell is keyed by day and start time, so a day cannot
            # have two slots beginning at the same hour.
            models.UniqueConstraint(
                fields=['day', 'start_time'],
                name='unique_timeslot_day_start',
            ),
        ]

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({
                'end_time': 'End time must be after the start time.',
            })

    def save(self, *args, **kwargs):
        # duration_hours is display-only and always recomputed from the two times.
        if self.start_time and self.end_time:
            self.clean()
            self.duration_hours = self.compute_duration_hours(self.start_time, self.end_time)
        super().save(*args, **kwargs)

    @staticmethod
    def compute_duration_hours(start_time, end_time):
        """Whole hours between two times, rounded half up, never below 1."""
        start_dt = datetime.combine(date.today(), start_time)
        end_dt = datetime.combine(date.today(), end_time)
        hours = Decimal(str((end_dt - start_dt).total_seconds() / 3600))
        return max(1, int(hours.quantize(Decimal('1'), rounding=ROUND_HALF_UP)))

    def __str__(self) -> str:
        label = f" - {self.label}" if self.label else ""
        return f"{self.get_day_display()} {self.start_time}-{self.end_time} ({self.get_slot_type_display()}){label}"


class StudentSchedule(models.Model):
    """
    Links a student to a subject with a specific time slot.
    Automatically generated when subjects are added to a student,
    ensuring no time conflicts (no two subjects overlap in the same slot).
    """

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="The student this schedule belongs to.",
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="The subject scheduled.",
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='student_schedules',
        help_text="The time slot for this subject.",
    )
    semester = models.CharField(
        max_length=50,
        blank=True,
        help_text="Semester (e.g., '1st Sem 2026').",
    )
    school_year = models.CharField(
        max_length=20,
        blank=True,
        help_text="School year (e.g., '2025-2026').",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student__id', day_rank('time_slot__day'), 'time_slot__start_time']
        unique_together = ('student', 'subject', 'semester', 'school_year')

    def __str__(self) -> str:
        return f"{self.student.id} - {self.subject.code} ({self.time_slot})"