"""
URL routing for schedules app.
"""

from rest_framework.routers import DefaultRouter

from .views import StudentScheduleViewSet, TimeSlotViewSet

router = DefaultRouter()
router.register(r'timeslots', TimeSlotViewSet, basename='timeslot')
router.register(r'schedules', StudentScheduleViewSet, basename='schedule')

urlpatterns = router.urls