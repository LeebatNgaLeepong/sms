"""
Admin panel registration for students app.
"""

from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Student model.
    """

    list_display = ('id', 'name', 'email', 'program', 'year_level', 'display_gpa', 'created_at')
    search_fields = ('id', 'name', 'email', 'program')
    list_filter = ('program', 'year_level')
    readonly_fields = ('id', 'display_gpa', 'created_at', 'updated_at')

    @admin.display(description="GPA")
    def display_gpa(self, obj):
        return obj.gpa
