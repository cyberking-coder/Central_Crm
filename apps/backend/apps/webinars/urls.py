from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceViewSet,
    WebinarRegistrationViewSet,
    WebinarViewSet,
)

webinar_router = DefaultRouter()
webinar_router.include_root_view = False
webinar_router.register("", WebinarViewSet, basename="webinar")

registrations_router = DefaultRouter()
registrations_router.include_root_view = False
registrations_router.register("", WebinarRegistrationViewSet,
                              basename="registration")

attendance_router = DefaultRouter()
attendance_router.include_root_view = False
attendance_router.register("", AttendanceViewSet, basename="attendance")

urlpatterns = [
    # Specific sub-paths first so they aren't mistaken for a Webinar PK.
    path("registrations/", include(registrations_router.urls)),
    path("attendance/", include(attendance_router.urls)),
    path("", include(webinar_router.urls)),
]
