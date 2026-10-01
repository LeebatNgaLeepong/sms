"""
URL routing for students app.
"""

from rest_framework.routers import DefaultRouter

from .request_views import EnrollmentRequestViewSet, MessageThreadViewSet
from .views import StudentViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'enrollment-requests', EnrollmentRequestViewSet, basename='enrollment-request')
router.register(r'threads', MessageThreadViewSet, basename='thread')

urlpatterns = router.urls
