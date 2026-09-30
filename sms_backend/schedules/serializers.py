"""
Serializers for schedules app.
"""

from django.conf import settings
from rest_framework import serializers

from .models import Section, StudentSchedule, TimeSlot
from .terms import InvalidTerm, resolve_term


class TermValidationMixin:
    """Rejects semesters and school years that are not configured options."""

    def validate_semester(self, value):
        return value

    def validate(self, attrs):
        try:
            semester, school_year = resolve_term(attrs)
        except InvalidTerm as exc:
            raise serializers.ValidationError({exc.field: [exc.message]})
        attrs['semester'] = semester
        attrs['school_year'] = school_year
        return attrs


class SectionSerializer(serializers.ModelSerializer):
    """
    Serializer for a section of a subject.
    """

    subject_code = serializers.CharField(source='subject.code', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    instructor_name = serializers.SerializerMethodField(read_only=True)
    enrolled_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Section
        fields = [
            'id',
            'subject',
            'subject_code',
            'subject_name',
            'code',
            'capacity',
            'instructor',
            'instructor_name',
            'enrolled_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_instructor_name(self, obj):
        if not obj.instructor:
            return None
        full = obj.instructor.get_full_name()
        return full or obj.instructor.username

    def get_enrolled_count(self, obj):
        return obj.students.count()


class TimeSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for TimeSlot model.
    """

    duration_hours = serializers.IntegerField(read_only=True)

    class Meta:
        model = TimeSlot
        fields = [
            'id',
            'day',
            'start_time',
            'end_time',
            'duration_hours',
            'slot_type',
            'label',
        ]
        read_only_fields = ['id', 'duration_hours']

    def validate(self, attrs):
        start = attrs.get('start_time') or getattr(self.instance, 'start_time', None)
        end = attrs.get('end_time') or getattr(self.instance, 'end_time', None)
        if start and end and end <= start:
            raise serializers.ValidationError({
                'end_time': 'End time must be after the start time.',
            })
        return attrs


class StudentScheduleSerializer(TermValidationMixin, serializers.ModelSerializer):
    """
    Serializer for StudentSchedule model with student, subject and section details.
    """

    student_id = serializers.CharField(source='student.id', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    section_code = serializers.SerializerMethodField(read_only=True)
    day = serializers.SerializerMethodField(read_only=True)
    start_time = serializers.SerializerMethodField(read_only=True)
    end_time = serializers.SerializerMethodField(read_only=True)
    duration_hours = serializers.SerializerMethodField(read_only=True)
    slot_type = serializers.SerializerMethodField(read_only=True)
    label = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StudentSchedule
        fields = [
            'id',
            'student',
            'student_id',
            'student_name',
            'subject',
            'subject_code',
            'subject_name',
            'section',
            'section_code',
            'time_slot',
            'day',
            'start_time',
            'end_time',
            'duration_hours',
            'slot_type',
            'label',
            'semester',
            'school_year',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def _slot_attr(self, obj, name):
        """Read a time slot attribute, tolerating an unscheduled entry."""
        return getattr(obj.time_slot, name, None) if obj.time_slot_id else None

    def get_section_code(self, obj):
        return obj.section.code if obj.section else None

    def get_day(self, obj):
        return self._slot_attr(obj, 'day')

    def get_start_time(self, obj):
        value = self._slot_attr(obj, 'start_time')
        return value.isoformat() if value else None

    def get_end_time(self, obj):
        value = self._slot_attr(obj, 'end_time')
        return value.isoformat() if value else None

    def get_duration_hours(self, obj):
        return self._slot_attr(obj, 'duration_hours')

    def get_slot_type(self, obj):
        return self._slot_attr(obj, 'slot_type')

    def get_label(self, obj):
        return self._slot_attr(obj, 'label')