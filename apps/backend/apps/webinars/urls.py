from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceViewSet,
    WebinarRegistrationViewSet,
    WebinarViewSet,
)

webinar_router = DefaultRouter()
webinar_router.register("", WebinarViewSet, basename="webinar")

sub_router = DefaultRouter()
sub_router.register("registrations", WebinarRegistrationViewSet,
                    basename="registration")
sub_router.register("attendance", AttendanceViewSet, basename="attendance")

urlpatterns = [
    # Sub-routes registered FIRST so "registrations"/"attendance" aren't
    # interpreted as webinar PKs.
    path("", include(sub_router.urls)),
    path("", include(webinar_router.urls)),
]
