"""
URL routing for students app.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .encryption_views import EncryptionKeyViewSet
from .request_views import EnrollmentRequestViewSet, MessageThreadViewSet
from .views import StudentViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'enrollment-requests', EnrollmentRequestViewSet, basename='enrollment-request')
router.register(r'threads', MessageThreadViewSet, basename='thread')
router.register(r'encryption-keys', EncryptionKeyViewSet, basename='encryption-key')

key_view = EncryptionKeyViewSet.as_view({
    'get': 'retrieve_me',
    'put': 'create',
    'post': 'create',
    'patch': 'create',
})

urlpatterns = [
    # Registered before the router so 'me' is not swallowed by the {pk} route.
    path('encryption-keys/me/', key_view, name='encryption-key-me'),
] + router.urls