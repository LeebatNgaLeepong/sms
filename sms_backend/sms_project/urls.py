"""
URL configuration for sms_project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # College Student Management System API Routes
    path('api/', include('accounts.urls')),
    path('api/', include('students.urls')),
    path('api/', include('subjects.urls')),
    path('api/', include('grades.urls')),
    path('api/', include('dashboard.urls')),
]
