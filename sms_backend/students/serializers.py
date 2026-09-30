"""
Serializers for students app.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Student

User = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for Student model with computed GPA and user linkage.
    """

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='student'),
        allow_null=True,
        required=False,
        help_text="User ID of the student's login account, if one exists.",
    )
    user_username = serializers.CharField(
        source='user.username',
        read_only=True,
        allow_null=True,
    )
    gpa = serializers.FloatField(
        read_only=True,
        help_text="Simple average of grade points across graded subjects.",
    )
    gwa = serializers.FloatField(
        read_only=True,
        help_text="General Weighted Average: grade points weighted by subject units.",
    )
    units_earned = serializers.IntegerField(read_only=True)
    sections = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Student
        fields = [
            'id',
            'user',
            'user_username',
            'name',
            'email',
            'program',
            'year_level',
            'gpa',
            'gwa',
            'units_earned',
            'sections',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'gpa', 'gwa', 'units_earned', 'sections',
                            'created_at', 'updated_at']

    def get_sections(self, obj):
        return [
            {
                'id': s.id,
                'code': s.code,
                'subject_code': s.subject.code,
                'subject_name': s.subject.name,
            }
            for s in obj.sections.select_related('subject')
        ]

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        query = Student.objects.filter(email__iexact=email)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("A student with this email already exists.")
        return email


class StudentGradesSummarySerializer(serializers.Serializer):
    """
    Serializer to represent all grades and computed GPA for a specific student.
    """

    student_id = serializers.CharField()
    student_name = serializers.CharField()
    email = serializers.EmailField()
    program = serializers.CharField()
    year_level = serializers.CharField()
    gpa = serializers.FloatField()
    gwa = serializers.FloatField()
    units_earned = serializers.IntegerField()
    total_grades = serializers.IntegerField()
    grades = serializers.ListField(child=serializers.DictField())
