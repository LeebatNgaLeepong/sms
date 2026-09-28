"""
Admin panel registration for subjects app.
"""

from django.contrib import admin
from .models import Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """
    Admin configuration for Subject model.
    """

    list_display = ('code', 'name', 'units', 'instructor', 'created_at')
    search_fields = ('code', 'name', 'instructor__username', 'instructor__first_name', 'instructor__last_name')
    list_filter = ('units',)
