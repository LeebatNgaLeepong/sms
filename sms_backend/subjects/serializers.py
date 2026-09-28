"""
Serializers for subjects app.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Subject

User = get_user_model()


class SubjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Subject model with instructor details and teacher role validation.
    """

    instructor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='teacher'),
        allow_null=True,
        required=False,
        help_text="User ID of the assigned teacher instructor.",
    )
    instructor_name = serializers.SerializerMethodField(
        read_only=True,
        help_text="Full display name or username of the instructor.",
    )
    instructor_email = serializers.EmailField(
        source='instructor.email',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Subject
        fields = [
            'id',
            'code',
            'name',
            'units',
            'instructor',
            'instructor_name',
            'instructor_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_instructor_name(self, obj) -> str | None:
        if obj.instructor:
            full_name = f"{obj.instructor.first_name} {obj.instructor.last_name}".strip()
            return full_name if full_name else obj.instructor.username
        return None

    def validate_code(self, value: str) -> str:
        code = value.strip().upper()
        if not code:
            raise serializers.ValidationError("Course code cannot be empty.")
        return code
