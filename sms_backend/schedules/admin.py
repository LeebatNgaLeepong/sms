"""
Admin panel registration for schedules app.

Lets staff edit class times and schedule entries directly at /admin/.
"""

from django.contrib import admin

from .models import StudentSchedule, TimeSlot


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """
    Admin configuration for TimeSlot.

    Set the start and end times directly; duration is derived from them. Editing a
    slot's times moves every class already assigned to it, so changing a time here
    reshuffles all students using that slot. Deleting a slot instead removes the
    schedule entries that referenced it.
    """

    list_display = ('day', 'start_time', 'end_time', 'duration_hours', 'slot_type', 'label', 'class_count')
    list_filter = ('day', 'slot_type', 'duration_hours')
    search_fields = ('label',)
    readonly_fields = ('duration_hours',)
    fields = ('day', 'start_time', 'end_time', 'duration_hours', 'slot_type', 'label')

    @admin.display(description='Scheduled classes')
    def class_count(self, obj):
        return obj.student_schedules.count()


@admin.register(StudentSchedule)
class StudentScheduleAdmin(admin.ModelAdmin):
    """
    Admin configuration for StudentSchedule.
    """

    list_display = (
        'student', 'subject', 'day', 'start_time_display', 'end_time_display',
        'slot_type_display', 'semester', 'school_year',
    )
    list_filter = ('time_slot__day', 'semester', 'school_year', 'time_slot__slot_type')
    search_fields = ('student__id', 'student__name', 'subject__code', 'subject__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('student', 'subject', 'time_slot')}),
        ('Term', {'fields': ('semester', 'school_year')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(description='Day', ordering='time_slot__day')
    def day(self, obj):
        return obj.time_slot.get_day_display()

    @admin.display(description='Start', ordering='time_slot__start_time')
    def start_time_display(self, obj):
        return obj.time_slot.start_time

    @admin.display(description='End')
    def end_time_display(self, obj):
        return obj.time_slot.end_time

    @admin.display(description='Type', ordering='time_slot__slot_type')
    def slot_type_display(self, obj):
        return obj.time_slot.get_slot_type_display()
