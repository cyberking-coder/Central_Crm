from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AdDashboardView,
    AdMetricsIngestView,
    CampaignViewSet,
    LeadSourceViewSet,
)

router = DefaultRouter()
router.register("lead-sources", LeadSourceViewSet, basename="lead-source")
router.register("campaigns", CampaignViewSet, basename="campaign")

urlpatterns = [
    *router.urls,
    path("marketing/ad-metrics/", AdMetricsIngestView.as_view(),
         name="ad-metrics-ingest"),
    path("marketing/ad-dashboard/", AdDashboardView.as_view(),
         name="ad-dashboard"),
]
