from django.urls import path

from .views import IntegrationsStatusView, RazorpayWebhookView

urlpatterns = [
    path("status/", IntegrationsStatusView.as_view(), name="integrations-status"),
    path("webhooks/razorpay/", RazorpayWebhookView.as_view(),
         name="webhook-razorpay"),
]
