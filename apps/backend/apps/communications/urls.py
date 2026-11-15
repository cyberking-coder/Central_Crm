from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CommunicationIngestView, CommunicationViewSet

router = DefaultRouter()
router.include_root_view = False
router.register("", CommunicationViewSet, basename="communication")

urlpatterns = [
    path("ingest/", CommunicationIngestView.as_view(),
         name="communication-ingest"),
    *router.urls,
]
