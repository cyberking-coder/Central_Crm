from rest_framework.routers import DefaultRouter

from .views import CampaignViewSet, LeadSourceViewSet

router = DefaultRouter()
router.register("lead-sources", LeadSourceViewSet, basename="lead-source")
router.register("campaigns", CampaignViewSet, basename="campaign")

urlpatterns = router.urls
