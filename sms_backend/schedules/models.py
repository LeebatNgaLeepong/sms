"""
Schedule models for College Student Management System.
Handles class schedules for students with automatic conflict-free generation.

Features:
- Time slots from 7:00 AM to 8:00 PM, Monday through Sunday
- Adjustable duration per subject session
- Lab or Lecture type designation
- Automatic conflict-free schedule generation
"""

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
    Each time slot has a start time, duration, and type (Lab or Lecture).
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
    duration_hours = models.PositiveSmallIntegerField(
        default=2,
        help_text="Duration of the slot in hours (e.g., 2 for 2 hours).",
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
        unique_together = ('day', 'start_time', 'duration_hours')

    @property
    def end_time(self):
        """Compute end time from start_time and duration_hours."""
        from datetime import datetime, timedelta
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = start_dt + timedelta(hours=self.duration_hours)
        return end_dt.time()

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