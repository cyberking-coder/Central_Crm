from django.urls import path
from rest_framework.routers import DefaultRouter

from .public_views import PublicLeadCaptureView
from .views import LeadViewSet

router = DefaultRouter()
router.include_root_view = False
router.register("", LeadViewSet, basename="lead")

urlpatterns = [
    path("public/", PublicLeadCaptureView.as_view(), name="lead-public"),
    *router.urls,
]
