from django.urls import path

from .views import (
    IntegrationsStatusView,
    RazorpayWebhookView,
    WebhookSubscriptionDetailView,
    WebhookSubscriptionsView,
)

urlpatterns = [
    path("status/", IntegrationsStatusView.as_view(), name="integrations-status"),
    path("webhooks/razorpay/", RazorpayWebhookView.as_view(),
         name="webhook-razorpay"),
    path("outbound-webhooks/", WebhookSubscriptionsView.as_view(),
         name="outbound-webhooks"),
    path("outbound-webhooks/<uuid:pk>/",
         WebhookSubscriptionDetailView.as_view(),
         name="outbound-webhook-detail"),
]
