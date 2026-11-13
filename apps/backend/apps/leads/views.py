from __future__ import annotations

from django.db.models import Q
from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.permissions import HasPermissionCode
from apps.audit.services import record_audit
from apps.core.exports import write_csv
from apps.employees.models import Employee

from .models import Lead
from .serializers import (
    LeadAssignSerializer,
    LeadAssignmentHistorySerializer,
    LeadSerializer,
    LeadStatusHistorySerializer,
)
from .services.assignment import assign_lead
from .services.conversion import ConversionError, convert_lead_to_customer
from .services.csv_import import import_leads_csv
from .services.duplicate_detection import find_duplicate_leads


ACTION_PERMISSION_MAP = {
    "list": "leads.read",
    "retrieve": "leads.read",
    "create": "leads.create",
    "update": "leads.update",
    "partial_update": "leads.update",
    "destroy": "leads.delete",
    "assign": "leads.assign",
    "convert": "leads.update",
    "export_csv": "leads.export",
    "import_csv": "leads.import",
    "duplicates": "leads.read",
    "history": "leads.read",
}


class LeadViewSet(viewsets.ModelViewSet):
    """
    Lead CRUD + assign / convert / import / export / duplicates / history.

    Queryset scoping:
    - Salesperson sees only leads assigned to their Employee profile.
    - Everyone else with leads.read sees all leads.
    """

    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter]
    filterset_fields = ["status", "priority", "source", "campaign",
                        "assigned_to"]
    search_fields = ["full_name", "email", "phone", "interested_product"]
    ordering_fields = ["created_at", "updated_at", "next_followup_at", "status"]
    ordering = ["-created_at"]

    def get_permissions(self):
        self.required_permission = ACTION_PERMISSION_MAP.get(
            self.action, "leads.read")
        return super().get_permissions()

    def get_queryset(self):
        qs = (Lead.objects
              .select_related("source", "campaign", "assigned_to")
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

    # ----- Standard create/update → audit emission -----

    def perform_create(self, serializer):
        lead = serializer.save()
        record_audit(actor=self.request.user, action="lead.created",
                     entity_type="Lead", entity_id=str(lead.pk),
                     after={"status": lead.status},
                     request=self.request)

    def perform_update(self, serializer):
        before_status = serializer.instance.status
        lead = serializer.save()
        if before_status != lead.status:
            from .models import LeadStatusHistory
            LeadStatusHistory.objects.create(
                lead=lead, from_status=before_status, to_status=lead.status,
                changed_by=self.request.user,
            )
            record_audit(actor=self.request.user, action="lead.status_changed",
                         entity_type="Lead", entity_id=str(lead.pk),
                         before={"status": before_status},
                         after={"status": lead.status},
                         request=self.request)

    def perform_destroy(self, instance):
        record_audit(actor=self.request.user, action="lead.deleted",
                     entity_type="Lead", entity_id=str(instance.pk),
                     request=self.request)
        instance.delete()

    # ----- Custom actions -----

    @extend_schema(request=LeadAssignSerializer, responses={200: LeadSerializer})
    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        lead = self.get_object()
        s = LeadAssignSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        emp_id = s.validated_data.get("employee_id")
        employee = Employee.objects.get(pk=emp_id) if emp_id else None
        assign_lead(lead=lead, to_employee=employee, actor=request.user,
                    reason=s.validated_data.get("reason", ""), request=request)
        return Response(LeadSerializer(lead).data)

    @extend_schema(responses={201: OpenApiResponse(description="Customer id")})
    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        lead = self.get_object()
        try:
            customer = convert_lead_to_customer(
                lead=lead, actor=request.user, request=request)
        except ConversionError as e:
            return Response({"detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({"customer_id": str(customer.pk)},
                        status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: OpenApiResponse(description="CSV file")})
    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())[:10_000]
        rows = [
            [str(l.pk), l.full_name, l.phone, l.email,
             l.source.name if l.source_id else "",
             l.status, l.priority,
             l.assigned_to.full_name if l.assigned_to_id else "",
             l.created_at.isoformat()]
            for l in qs
        ]
        data = write_csv(
            ["id", "full_name", "phone", "email", "source",
             "status", "priority", "assigned_to", "created_at"],
            rows,
        )
        record_audit(actor=request.user, action="leads.exported",
                     entity_type="Lead",
                     extra={"count": len(rows)}, request=request)
        resp = HttpResponse(data, content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="leads.csv"'
        return resp

    @extend_schema(responses={200: dict})
    @action(detail=False, methods=["post"], url_path="import")
    def import_csv(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"detail": "Upload a CSV file as 'file'."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            report = import_leads_csv(file_obj=upload, actor=request.user,
                                      request=request)
        except ValueError as e:
            return Response({"detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "total_rows": report.total_rows,
            "created": report.created,
            "duplicates_skipped": report.duplicates_skipped,
            "failed": report.failed,
        })

    @extend_schema(responses={200: LeadSerializer(many=True)})
    @action(detail=False, methods=["get"])
    def duplicates(self, request):
        """Given phone/email query params, list potential duplicates."""
        phone = request.query_params.get("phone")
        email = request.query_params.get("email")
        qs = find_duplicate_leads(phone=phone, email=email)
        return Response(LeadSerializer(qs, many=True).data)

    @extend_schema(responses={200: dict})
    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        lead = self.get_object()
        return Response({
            "assignments": LeadAssignmentHistorySerializer(
                lead.assignment_history.all(), many=True).data,
            "statuses": LeadStatusHistorySerializer(
                lead.status_history.all(), many=True).data,
        })
