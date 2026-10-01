"""
Serializers for grades app.
Handles validation of score ranges, server-side derivation of letter & grade points,
unique constraint validation, and teacher assignment verification.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import serializers

from students.models import Student
from subjects.models import Subject
from .models import Grade, compute_grade_details

User = get_user_model()


class GradeSerializer(serializers.ModelSerializer):
    """
    Serializer for recording and updating student grades.
    Enforces server-side derivation of letter grade and grade points,
    validates score range (0-100), and restricts teachers to assigned subjects.
    """

    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        help_text="Student ID (e.g., STU-10001).",
    )
    student_name = serializers.CharField(
        source='student.name',
        read_only=True,
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        help_text="Subject ID.",
    )
    subject_code = serializers.CharField(
        source='subject.code',
        read_only=True,
    )
    subject_name = serializers.CharField(
        source='subject.name',
        read_only=True,
    )
    score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00'),
        required=False,
        allow_null=True,
        help_text="Numerical score between 0.00 and 100.00. Leave empty when marking INC.",
    )
    is_incomplete = serializers.BooleanField(
        required=False,
        help_text="Mark the subject as not completed yet. Recorded as INC with no grade points.",
    )
    letter = serializers.CharField(
        read_only=True,
        help_text="Server-computed grade (1.00 ... 5.00, or INC).",
    )
    grade_points = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        read_only=True,
        allow_null=True,
        help_text="Server-computed grade points (1.00=best, 3.00=pass, 5.00=fail). Empty for INC.",
    )
    recorded_by = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )
    recorded_by_username = serializers.CharField(
        source='recorded_by.username',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Grade
        fields = [
            'id',
            'student',
            'student_name',
            'subject',
            'subject_code',
            'subject_name',
            'score',
            'is_incomplete',
            'letter',
            'grade_points',
            'recorded_by',
            'recorded_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'letter',
            'grade_points',
            'recorded_by',
            'recorded_by_username',
            'created_at',
            'updated_at',
        ]

    def validate_score(self, value: Decimal) -> Decimal:
        if value < Decimal('0.00') or value > Decimal('100.00'):
            raise serializers.ValidationError("Score must be between 0.00 and 100.00.")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        student = attrs.get('student') or getattr(self.instance, 'student', None)
        subject = attrs.get('subject') or getattr(self.instance, 'subject', None)
        score = attrs.get('score') if 'score' in attrs else getattr(self.instance, 'score', None)
        is_incomplete = attrs.get(
            'is_incomplete',
            getattr(self.instance, 'is_incomplete', False),
        )

        if not student or not subject:
            raise serializers.ValidationError("Both student and subject must be provided.")

        # An INC grade has no score, and a scored grade must have one.
        if is_incomplete:
            if score is not None:
                raise serializers.ValidationError({
                    'score': 'An INC grade has no score. Clear the score first.'
                })
            attrs['score'] = None
        elif score is None:
            raise serializers.ValidationError({
                'score': 'Enter a score, or mark this grade as INC.'
            })

        # Check unique constraint (student, subject)
        existing_grade = Grade.objects.filter(student=student, subject=subject)
        if self.instance:
            existing_grade = existing_grade.exclude(pk=self.instance.pk)
        if existing_grade.exists():
            raise serializers.ValidationError(
                {"detail": f"A grade for {student.name} in {subject.code} already exists."}
            )

        # Enforce teacher role restriction: can only grade assigned subjects
        if user and user.is_authenticated and user.role == 'teacher' and not user.is_superuser:
            if subject.instructor != user:
                raise serializers.ValidationError(
                    {"subject": f"You are only permitted to record or modify grades for subjects you teach ({user.username})."}
                )

        # Auto-compute letter and grade_points for payload preview/consistency
        if not is_incomplete and score is not None:
            letter, points = compute_grade_details(score)
            attrs['letter'] = letter
            attrs['grade_points'] = points

        return attrs
