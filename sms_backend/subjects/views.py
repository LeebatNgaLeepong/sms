"""
ViewSets for subjects app.
"""

from rest_framework import filters, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import SubjectPermission
from .models import Subject
from .serializers import SubjectSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Subject management:
    - GET /api/subjects/ : list all subjects (any authenticated user)
    - POST /api/subjects/ : create a new subject (Admin only)
    - GET /api/subjects/{id}/ : retrieve details of a subject (any authenticated user)
    - PUT/PATCH/DELETE /api/subjects/{id}/ : modify or remove a subject (Admin only)
    """

    queryset = Subject.objects.select_related('instructor').all()
    serializer_class = SubjectSerializer
    permission_classes = [SubjectPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name']
    filterset_fields = ['instructor', 'units']
    ordering_fields = ['code', 'name', 'units', 'created_at']
    ordering = ['code']
