from __future__ import annotations

import json
import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.accounts.permissions import HasPermissionCode
from apps.finance.models import WebhookEvent
from apps.finance.services.webhooks import ingest_webhook_event

from .adapters import email_adapter, razorpay, whatsapp
from .outbound import EVENT_CHOICES, WebhookSubscription

log = logging.getLogger(__name__)


class _WebhookThrottle(AnonRateThrottle):
    scope = "webhook"


@method_decorator(csrf_exempt, name="dispatch")
class RazorpayWebhookView(APIView):
    """
    Razorpay POSTs here. Signature is verified before anything else; a
    bad signature returns 400 and the event is NOT stored (otherwise
    attackers could burn dedup keys).
    """
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [_WebhookThrottle]

    def post(self, request):
        raw = request.body or b""
        sig = request.META.get("HTTP_X_RAZORPAY_SIGNATURE", "")
        if not razorpay.verify_signature(raw_body=raw, provided=sig):
            log.warning("razorpay: invalid signature")
            return Response({"detail": "Invalid signature"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON"},
                            status=status.HTTP_400_BAD_REQUEST)

        event_id = payload.get("id") or payload.get("event_id") or ""
        event_type = payload.get("event") or payload.get("type") or ""
        if not event_id or not event_type:
            return Response({"detail": "Missing id or event type."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            was_new, event, result = ingest_webhook_event(
                provider=razorpay.PROVIDER,
                provider_event_id=event_id,
                event_type=event_type,
                payload=payload,
                handler=razorpay.handle_event,
            )
        except Exception:
            # Idempotency row is already marked FAILED; let Razorpay retry.
            return Response({"detail": "Processing failed"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"ok": True, "duplicate": not was_new,
                         "event_id": str(event.id), "result": result or {}})


class WebhookSubscriptionsView(APIView):
    """List / create outbound webhook subscriptions."""
    permission_classes = [IsAuthenticated, HasPermissionCode]

    def get_permissions(self):
        self.required_permission = (
            "integrations.read" if self.request.method == "GET"
            else "integrations.manage"
        )
        return super().get_permissions()

    def get(self, request):
        subs = WebhookSubscription.objects.all()
        return Response({
            "available_events": [{"code": c, "label": l}
                                  for c, l in EVENT_CHOICES],
            "results": [self._serialise(s) for s in subs],
        })

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        url = (request.data.get("url") or "").strip()
        events = request.data.get("events") or []
        if not name or not url:
            return Response({"detail": "name and url are required"},
                            status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(events, list) or not events:
            return Response({"detail": "events must be a non-empty list"},
                            status=status.HTTP_400_BAD_REQUEST)
        from .outbound import ALL_EVENTS
        bad = [e for e in events if e not in ALL_EVENTS]
        if bad:
            return Response({"detail": f"unknown events: {bad}"},
                            status=status.HTTP_400_BAD_REQUEST)
        sub = WebhookSubscription(
            name=name, url=url, events=events,
            created_by=request.user,
        )
        sub.generate_secret()
        sub.save()
        return Response({**self._serialise(sub), "secret": sub.secret},
                        status=status.HTTP_201_CREATED)

    @staticmethod
    def _serialise(s):
        return {
            "id": str(s.id),
            "name": s.name,
            "url": s.url,
            "events": s.events,
            "is_active": s.is_active,
            "failure_count": s.failure_count,
            "last_delivery_at": s.last_delivery_at.isoformat()
            if s.last_delivery_at else None,
            "last_delivery_status": s.last_delivery_status,
            "last_error": s.last_error,
            "created_at": s.created_at.isoformat(),
        }


class WebhookSubscriptionDetailView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "integrations.manage"

    def delete(self, request, pk):
        try:
            sub = WebhookSubscription.objects.get(pk=pk)
        except WebhookSubscription.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        sub.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IntegrationsStatusView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "integrations.read"

    def get(self, request):
        rows = []
        # Razorpay
        last = WebhookEvent.objects.filter(provider="razorpay").order_by(
            "-received_at").values_list("received_at", flat=True).first()
        rows.append({
            "name": "razorpay",
            "label": "Razorpay payments",
            "enabled": razorpay.is_configured(),
            "configured": razorpay.is_configured(),
            "last_event_at": last.isoformat() if last else None,
            "details": "Set RAZORPAY_WEBHOOK_SECRET to enable.",
        })
        # Email
        rows.append({
            "name": "email",
            "label": "Outbound email (SMTP)",
            "enabled": email_adapter.is_configured(),
            "configured": email_adapter.is_configured(),
            "last_event_at": None,
            "details": "Set EMAIL_HOST / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD.",
        })
        # WhatsApp
        rows.append({
            "name": "whatsapp",
            "label": "WhatsApp Business",
            "enabled": False,  # stub; real send off until adapter is wired
            "configured": whatsapp.is_configured(),
            "last_event_at": None,
            "details": "Stub adapter; set WHATSAPP_PHONE_NUMBER_ID + "
                        "WHATSAPP_ACCESS_TOKEN to prepare config.",
        })
        return Response({"integrations": rows})
