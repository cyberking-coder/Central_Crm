from rest_framework.routers import DefaultRouter

from .views import FollowUpViewSet, SalesActivityViewSet

router = DefaultRouter()
router.register("activities", SalesActivityViewSet, basename="activity")
router.register("followups", FollowUpViewSet, basename="followup")

urlpatterns = router.urls
