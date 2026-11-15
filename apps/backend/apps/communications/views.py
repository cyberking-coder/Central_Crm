from __future__ import annotations

from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasPermissionCode
from apps.customers.models import Customer
from apps.leads.models import Lead

from .models import Communication
from .serializers import (
    CommunicationIngestSerializer,
    CommunicationSerializer,
)
from .services import resolve_lead_or_customer


PERMS = {
    "list": "customers.read", "retrieve": "customers.read",
    "create": "sales.activity.create",
    "update": "sales.activity.update",
    "partial_update": "sales.activity.update",
    "destroy": "sales.activity.update",
}


class CommunicationViewSet(viewsets.ModelViewSet):
    serializer_class = CommunicationSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["lead", "customer", "channel", "direction"]
    ordering_fields = ["occurred_at", "created_at"]
    ordering = ["-occurred_at"]

    def get_permissions(self):
        self.required_permission = PERMS.get(self.action, "customers.read")
        return super().get_permissions()

    def get_queryset(self):
        return Communication.objects.select_related(
            "lead", "customer", "employee").all()


class CommunicationIngestView(APIView):
    """
    Idempotent ingest endpoint for n8n / email relays / telephony hooks.

    Accepts a single event with `lead_id`, `customer_id`, or raw
    `contact_email` / `contact_phone` (which we match against the CRM).
    Returns 200 with the created or deduped row.
    """
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "sales.activity.create"

    def post(self, request):
        s = CommunicationIngestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        lead = None
        customer = None
        if data.get("lead_id"):
            lead = Lead.objects.filter(pk=data["lead_id"]).first()
        if data.get("customer_id"):
            customer = Customer.objects.filter(pk=data["customer_id"]).first()
        if lead is None and customer is None:
            lead, customer = resolve_lead_or_customer(
                email=data.get("contact_email", ""),
                phone=data.get("contact_phone", ""),
            )
        if lead is None and customer is None:
            return Response(
                {"detail": "Could not match contact to any lead or customer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        external_ref = data.get("external_ref", "")
        channel = data["channel"]

        # Idempotent: if already ingested, return existing row.
        if external_ref:
            existing = Communication.objects.filter(
                channel=channel, external_ref=external_ref).first()
            if existing is not None:
                return Response(
                    {**CommunicationSerializer(existing).data,
                     "duplicate": True},
                    status=status.HTTP_200_OK,
                )

        try:
            comm = Communication.objects.create(
                lead=lead, customer=customer,
                channel=channel, direction=data["direction"],
                from_address=data.get("from_address", ""),
                to_address=data.get("to_address", ""),
                subject=data.get("subject", ""),
                body=data.get("body", ""),
                attachments=data.get("attachments", []),
                duration_seconds=data.get("duration_seconds"),
                recording_url=data.get("recording_url", ""),
                external_ref=external_ref,
                occurred_at=data["occurred_at"],
                pushed_by=request.user,
            )
        except IntegrityError:
            # Race with another ingest for the same ref.
            comm = Communication.objects.get(
                channel=channel, external_ref=external_ref)
            return Response(
                {**CommunicationSerializer(comm).data, "duplicate": True},
                status=status.HTTP_200_OK,
            )

        return Response(CommunicationSerializer(comm).data,
                        status=status.HTTP_201_CREATED)
