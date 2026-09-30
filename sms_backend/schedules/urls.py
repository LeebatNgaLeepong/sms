"""
URL routing for schedules app.
"""

from rest_framework.routers import DefaultRouter

from .views import (
    SectionViewSet,
    StudentScheduleViewSet,
    TermOptionsView,
    TimeSlotViewSet,
)

router = DefaultRouter()
router.register(r'timeslots', TimeSlotViewSet, basename='timeslot')
router.register(r'sections', SectionViewSet, basename='section')
router.register(r'schedules', StudentScheduleViewSet, basename='schedule')
router.register(r'terms', TermOptionsView, basename='term')

urlpatterns = router.urls
