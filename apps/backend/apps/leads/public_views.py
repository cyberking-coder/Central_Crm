"""
Public, unauthenticated lead capture (Phase 8).

Used by website forms. Captures the lead, normalises contact fields,
resolves source + campaign by UTM, and applies the duplicate rule — a
duplicate contact returns 200 OK silently so the form never leaks that
the person is already in the system.
"""
from __future__ import annotations

from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_audit
from apps.core.normalisation import normalise_email, normalise_phone
from apps.marketing.models import Campaign, LeadSource

from .models import Lead
from .services.duplicate_detection import find_duplicate_leads


class _PublicLeadThrottle(AnonRateThrottle):
    scope = "public_leads"


class _PublicLeadSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    interested_product = serializers.CharField(max_length=200, required=False,
                                                allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    # UTM / attribution
    source = serializers.CharField(max_length=80, required=False, allow_blank=True,
                                    help_text="LeadSource slug.")
    utm_source = serializers.CharField(max_length=80, required=False, allow_blank=True)
    utm_medium = serializers.CharField(max_length=80, required=False, allow_blank=True)
    utm_campaign = serializers.CharField(max_length=120, required=False, allow_blank=True)


class PublicLeadCaptureView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [_PublicLeadThrottle]

    def post(self, request):
        s = _PublicLeadSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        # Resolve source.
        source = None
        slug = (data.get("source") or "").strip().lower()
        if slug:
            source = LeadSource.objects.filter(slug=slug).first()
        if source is None and data.get("utm_source"):
            source = LeadSource.objects.filter(
                slug=data["utm_source"].strip().lower()).first()
        if source is None:
            source = LeadSource.objects.filter(slug="website").first() \
                or LeadSource.objects.filter(slug="other").first()

        # Resolve campaign by utm_campaign (case-insensitive).
        campaign = None
        if data.get("utm_campaign"):
            campaign = Campaign.objects.filter(
                utm_campaign__iexact=data["utm_campaign"],
                is_active=True,
            ).first() or Campaign.objects.filter(
                name__iexact=data["utm_campaign"], is_active=True,
            ).first()

        phone = data.get("phone", "")
        email = data.get("email", "")
        pn = normalise_phone(phone)
        en = normalise_email(email)

        # Dedup — do not leak existence.
        if pn or en:
            dupes = find_duplicate_leads(phone=phone, email=email)
            if dupes.exists():
                record_audit(actor=None, action="lead.public_duplicate",
                             entity_type="Lead", request=request,
                             extra={"email": email, "phone": phone})
                return Response({"ok": True}, status=status.HTTP_200_OK)

        lead = Lead.objects.create(
            full_name=data["full_name"],
            phone=phone, phone_normalised=pn,
            email=email, email_normalised=en,
            interested_product=data.get("interested_product", ""),
            notes=data.get("notes", ""),
            source=source, campaign=campaign,
            status=Lead.Status.NEW,
        )
        record_audit(actor=None, action="lead.public_created",
                     entity_type="Lead", entity_id=str(lead.pk),
                     request=request,
                     extra={"source": source.slug if source else None,
                            "utm_campaign": data.get("utm_campaign", "")})
        return Response({"ok": True, "lead_id": str(lead.pk)},
                        status=status.HTTP_201_CREATED)
