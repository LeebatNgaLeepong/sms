"""
Admin panel registration for grades app.
"""

from django.contrib import admin
from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """
    Admin configuration for Grade model.
    """

    list_display = ('student', 'subject', 'score', 'letter', 'grade_points', 'recorded_by', 'updated_at')
    search_fields = ('student__id', 'student__name', 'subject__code', 'subject__name')
    list_filter = ('letter', 'subject')
    readonly_fields = ('letter', 'grade_points', 'created_at', 'updated_at')
