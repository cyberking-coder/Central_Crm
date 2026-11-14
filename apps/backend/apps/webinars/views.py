from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import HasPermissionCode
from apps.audit.services import record_audit
from apps.customers.models import Customer
from apps.leads.models import Lead
from apps.marketing.models import LeadSource

from .models import Webinar, WebinarAttendance, WebinarRegistration
from .serializers import (
    AttendanceSerializer,
    AttendanceUpdateSerializer,
    RegistrationCreateSerializer,
    RegistrationSerializer,
    WebinarSerializer,
)
from .services.attendance import record_attendance, webinar_summary
from .services.registration import RegistrationError, register_for_webinar


WEBINAR_PERMS = {
    "list": "webinars.read", "retrieve": "webinars.read",
    "create": "webinars.manage", "update": "webinars.manage",
    "partial_update": "webinars.manage", "destroy": "webinars.manage",
    "register": "webinars.manage", "stats": "webinars.read",
    "registrations": "webinars.read",
}

REG_PERMS = {
    "list": "webinars.read", "retrieve": "webinars.read",
    "destroy": "webinars.attendance",
}

ATT_PERMS = {
    "list": "webinars.read", "retrieve": "webinars.read",
    "update": "webinars.attendance",
    "partial_update": "webinars.attendance",
}


class WebinarViewSet(viewsets.ModelViewSet):
    serializer_class = WebinarSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter]
    filterset_fields = ["status", "host", "manager"]
    search_fields = ["title", "description"]
    ordering_fields = ["start_at", "created_at", "title"]
    ordering = ["-start_at"]

    def get_permissions(self):
        self.required_permission = WEBINAR_PERMS.get(
            self.action, "webinars.read")
        return super().get_permissions()

    def get_queryset(self):
        return Webinar.objects.select_related("host", "manager").all()

    def perform_create(self, serializer):
        obj = serializer.save(created_by=self.request.user)
        record_audit(actor=self.request.user, action="webinar.created",
                     entity_type="Webinar", entity_id=str(obj.pk),
                     request=self.request)

    def perform_update(self, serializer):
        obj = serializer.save()
        record_audit(actor=self.request.user, action="webinar.updated",
                     entity_type="Webinar", entity_id=str(obj.pk),
                     request=self.request)

    def perform_destroy(self, instance):
        record_audit(actor=self.request.user, action="webinar.deleted",
                     entity_type="Webinar", entity_id=str(instance.pk),
                     request=self.request)
        instance.delete()

    @extend_schema(request=RegistrationCreateSerializer,
                   responses={201: RegistrationSerializer,
                              400: OpenApiResponse(description="Capacity / duplicate")})
    @action(detail=True, methods=["post"])
    def register(self, request, pk=None):
        webinar = self.get_object()
        s = RegistrationCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        lead = Lead.objects.filter(pk=data.get("lead")).first() \
            if data.get("lead") else None
        customer = Customer.objects.filter(pk=data.get("customer")).first() \
            if data.get("customer") else None
        source = LeadSource.objects.filter(pk=data.get("registration_source")).first() \
            if data.get("registration_source") else None

        try:
            reg = register_for_webinar(
                webinar=webinar, full_name=data["full_name"],
                phone=data.get("phone", ""), email=data.get("email", ""),
                lead=lead, customer=customer, source=source,
                external_ref=data.get("external_ref", ""),
                actor=request.user, request=request,
            )
        except RegistrationError as e:
            return Response({"detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(RegistrationSerializer(reg).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def registrations(self, request, pk=None):
        webinar = self.get_object()
        qs = (webinar.registrations
              .select_related("attendance", "registration_source",
                              "lead", "customer").all())
        return Response(RegistrationSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        return Response(webinar_summary(self.get_object()))


class WebinarRegistrationViewSet(viewsets.ReadOnlyModelViewSet):
    """Flat registration listing (filterable by webinar)."""
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["webinar", "status", "lead", "customer"]

    def get_permissions(self):
        self.required_permission = REG_PERMS.get(self.action, "webinars.read")
        return super().get_permissions()

    def get_queryset(self):
        return WebinarRegistration.objects.select_related(
            "attendance", "webinar", "registration_source").all()


from rest_framework import mixins


class AttendanceViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "registration__webinar"]

    def get_permissions(self):
        self.required_permission = ATT_PERMS.get(self.action, "webinars.read")
        return super().get_permissions()

    def get_queryset(self):
        return (WebinarAttendance.objects
                .select_related("registration__webinar").all())

    def update(self, request, *args, **kwargs):
        attendance = self.get_object()
        s = AttendanceUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        record_attendance(attendance=attendance, actor=request.user,
                          request=request, **s.validated_data)
        return Response(AttendanceSerializer(attendance).data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
