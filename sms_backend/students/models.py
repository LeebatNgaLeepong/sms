"""
Students models for College Student Management System.
"""

import random
from django.conf import settings
from django.db import models


def generate_student_id() -> str:
    """
    Generate an auto display ID in STU-XXXXX format.
    Prefers sequential numbering starting at STU-10001; falls back to random 5-digit on collisions.
    """
    from .models import Student
    last_student = Student.objects.filter(id__startswith='STU-').order_by('id').last()
    if last_student:
        try:
            val = int(last_student.id.split('-')[1])
            candidate = f"STU-{val + 1:05d}"
            if not Student.objects.filter(id=candidate).exists():
                return candidate
        except (IndexError, ValueError):
            pass

    # Fallback to random 5-digit STU-XXXXX
    for _ in range(100):
        candidate = f"STU-{random.randint(10000, 99999)}"
        if not Student.objects.filter(id=candidate).exists():
            return candidate

    # Extreme fallback with timestamp
    import time
    return f"STU-{int(time.time()) % 100000:05d}"


class Student(models.Model):
    """
    Student model representing enrolled students.
    May be linked optionally to a User account for login.
    """

    id = models.CharField(
        max_length=20,
        primary_key=True,
        editable=False,
        help_text="Custom student identifier (e.g., STU-10001).",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile',
        help_text="Optional login account for this student.",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    program = models.CharField(
        max_length=120,
        help_text="Degree program (e.g., BS Computer Science).",
    )
    year_level = models.CharField(
        max_length=50,
        help_text="Current academic year (e.g., 1st Year, 2nd Year).",
    )
    enrolled_subjects = models.ManyToManyField(
        'subjects.Subject',
        blank=True,
        related_name='enrolled_students',
        help_text="Subjects this student is currently enrolled in.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_student_id()
        super().save(*args, **kwargs)

    @property
    def gpa(self) -> float:
        """
        Simple average of grade_points across all graded subjects.
        Uses University of Antique scale (1.00 = best, 5.00 = fail).
        INC grades carry no points and are excluded.
        Returns 5.00 if the student has no graded subjects yet.
        """
        grades = self.grades.filter(grade_points__isnull=False)
        if not grades.exists():
            return 5.00
        avg_points = grades.aggregate(models.Avg('grade_points'))['grade_points__avg']
        return round(float(avg_points or 5.00), 2)

    @property
    def gwa(self) -> float:
        """
        General Weighted Average: grade points weighted by subject units, which is
        the figure of merit the university reports.

            GWA = sum(grade_points x units) / sum(units)

        INC grades are excluded because the subject is not finished.
        Returns 5.00 when the student has no graded subjects.
        """
        from decimal import Decimal

        total_units = 0
        weighted = Decimal('0')
        for grade in self.grades.filter(grade_points__isnull=False).select_related('subject'):
            units = grade.subject.units or 0
            if units <= 0:
                continue
            total_units += units
            weighted += Decimal(str(grade.grade_points)) * units

        if total_units == 0:
            return 5.00
        return round(float(weighted / Decimal(total_units)), 2)

    @property
    def units_earned(self) -> int:
        """Total credit units across graded subjects (INC excluded)."""
        return sum(
            (g.subject.units or 0)
            for g in self.grades.filter(grade_points__isnull=False).select_related('subject')
        )

    @property
    def incomplete_count(self) -> int:
        """How many of this student's subjects are still marked INC."""
        return self.grades.filter(is_incomplete=True).count()

    def __str__(self) -> str:
        return f"{self.id} - {self.name}"


class EnrollmentRequest(models.Model):
    """
    A student's request to add a subject to their load for a term.

    Staff approve or reject it. Approving enrolls the student and rebuilds their
    timetable, so a request is the only way a student can change their own load.
    """

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollment_requests',
        help_text="Student who made the request.",
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='enrollment_requests',
        help_text="Subject the student wants to take.",
    )
    semester = models.CharField(max_length=50, blank=True)
    school_year = models.CharField(max_length=20, blank=True)
    reason = models.TextField(
        blank=True,
        help_text="Why the student wants this subject.",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_enrollment_requests',
        help_text="Staff member who approved or rejected the request.",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # One live request per subject per term; decided ones can be repeated.
            models.UniqueConstraint(
                fields=['student', 'subject', 'semester', 'school_year'],
                condition=models.Q(status='pending'),
                name='unique_pending_enrollment_request',
            ),
        ]

    def __str__(self) -> str:
        return f"{self.student_id} -> {self.subject_id} ({self.get_status_display()})"


class MessageThread(models.Model):
    """
    A private conversation between one student and one of their teachers.
    """

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='message_threads',
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_threads',
        limit_choices_to={'role': 'teacher'},
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_threads',
        help_text="Optional subject this thread is about.",
    )
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at', '-created_at']
        unique_together = ('student', 'teacher')

    def other_party(self, user):
        """The participant on the other end of the thread from `user`."""
        return self.teacher if user == self.student.user else self.student

    def unread_for(self, user) -> int:
        """Messages in this thread the given user has not read."""
        return self.messages.exclude(sender=user).filter(read_at__isnull=True).count()

    def __str__(self) -> str:
        return f"{self.student_id} <-> {self.teacher.username}"


class Message(models.Model):
    """
    A single message inside a thread.
    """

    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    body = models.TextField()
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the other participant read this message.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.sender.username}: {self.body[:40]}"
