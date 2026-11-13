from __future__ import annotations

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.permissions import HasPermissionCode
from apps.audit.services import record_audit
from apps.core.exports import write_csv

from .models import Customer
from .serializers import CustomerSerializer, CustomerTimelineSerializer


ACTION_PERMISSION_MAP = {
    "list": "customers.read",
    "retrieve": "customers.read",
    "create": "customers.create",
    "update": "customers.update",
    "partial_update": "customers.update",
    "destroy": "customers.delete",
    "export_csv": "customers.export",
    "timeline": "customers.read",
}


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter]
    filterset_fields = ["status", "source", "assigned_to"]
    search_fields = ["full_name", "email", "phone"]
    ordering_fields = ["created_at", "updated_at", "full_name"]
    ordering = ["-created_at"]

    def get_permissions(self):
        self.required_permission = ACTION_PERMISSION_MAP.get(
            self.action, "customers.read")
        return super().get_permissions()

    def get_queryset(self):
        qs = (Customer.objects
              .select_related("source", "assigned_to")
              .all())
        user = self.request.user
        if user.is_superuser:
            return qs
        role_name = user.role.name if user.role_id else None
        if role_name == "Salesperson":
            employee = getattr(user, "employee", None)
            if employee is None:
                return qs.none()
            return qs.filter(assigned_to=employee)
        return qs

    def perform_create(self, serializer):
        customer = serializer.save()
        record_audit(actor=self.request.user, action="customer.created",
                     entity_type="Customer", entity_id=str(customer.pk),
                     request=self.request)

    def perform_update(self, serializer):
        customer = serializer.save()
        record_audit(actor=self.request.user, action="customer.updated",
                     entity_type="Customer", entity_id=str(customer.pk),
                     request=self.request)

    def perform_destroy(self, instance):
        record_audit(actor=self.request.user, action="customer.deleted",
                     entity_type="Customer", entity_id=str(instance.pk),
                     request=self.request)
        instance.delete()

    @extend_schema(responses={200: CustomerTimelineSerializer(many=True)})
    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        customer = self.get_object()
        events = customer.timeline.select_related("actor").all()
        return Response(CustomerTimelineSerializer(events, many=True).data)

    @extend_schema(responses={200: OpenApiResponse(description="CSV file")})
    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())[:10_000]
        rows = [
            [str(c.pk), c.full_name, c.phone, c.email,
             c.source.name if c.source_id else "",
             c.status,
             c.assigned_to.full_name if c.assigned_to_id else "",
             c.created_at.isoformat()]
            for c in qs
        ]
        data = write_csv(
            ["id", "full_name", "phone", "email", "source", "status",
             "assigned_to", "created_at"],
            rows,
        )
        record_audit(actor=request.user, action="customers.exported",
                     entity_type="Customer",
                     extra={"count": len(rows)}, request=request)
        resp = HttpResponse(data, content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="customers.csv"'
        return resp
