"""
Serializers for schedules app.
"""

from rest_framework import serializers

from .models import StudentSchedule, TimeSlot


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


class StudentScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for StudentSchedule model with student and subject details.
    """

    student_id = serializers.CharField(source='student.id', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    day = serializers.CharField(source='time_slot.day', read_only=True)
    start_time = serializers.TimeField(source='time_slot.start_time', read_only=True)
    duration_hours = serializers.IntegerField(source='time_slot.duration_hours', read_only=True)
    slot_type = serializers.CharField(source='time_slot.slot_type', read_only=True)
    end_time = serializers.SerializerMethodField(read_only=True)
    label = serializers.CharField(source='time_slot.label', read_only=True)

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
            'time_slot',
            'day',
            'start_time',
            'duration_hours',
            'slot_type',
            'end_time',
            'label',
            'semester',
            'school_year',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_end_time(self, obj):
        """Return the time slot's end time."""
        end = obj.time_slot.end_time
        return end.isoformat() if end else None