from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from .views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("auth/", include("apps.accounts.urls")),
    path("leads/", include("apps.leads.urls")),
    path("customers/", include("apps.customers.urls")),
    path("sales/", include("apps.sales.urls")),
    path("tasks/", include("apps.tasks.urls")),
    path("webinars/", include("apps.webinars.urls")),
    path("finance/", include("apps.finance.urls")),
    path("integrations/", include("apps.integrations.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("", include("apps.marketing.urls")),
]
