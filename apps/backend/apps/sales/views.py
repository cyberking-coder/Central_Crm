from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import HasPermissionCode
from apps.audit.services import record_audit

from .models import FollowUp, SalesActivity
from .serializers import FollowUpSerializer, SalesActivitySerializer
from .services.activities import record_activity
from .services.followups import cancel_followup, complete_followup


ACT_PERMS = {
    "list": "sales.activity.read", "retrieve": "sales.activity.read",
    "create": "sales.activity.create",
    "update": "sales.activity.update", "partial_update": "sales.activity.update",
    "destroy": "sales.activity.update",
}

FU_PERMS = {
    "list": "sales.followup.read", "retrieve": "sales.followup.read",
    "create": "sales.followup.manage",
    "update": "sales.followup.manage", "partial_update": "sales.followup.manage",
    "destroy": "sales.followup.manage",
    "complete": "sales.followup.manage", "cancel": "sales.followup.manage",
}


def _scope_by_salesperson(qs, user, assigned_field):
    role = user.role.name if user.role_id else None
    if role == "Salesperson":
        emp = getattr(user, "employee", None)
        if emp is None:
            return qs.none()
        return qs.filter(**{assigned_field: emp})
    return qs


class SalesActivityViewSet(viewsets.ModelViewSet):
    serializer_class = SalesActivitySerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["kind", "lead", "customer", "performed_by"]
    ordering_fields = ["occurred_at", "created_at"]
    ordering = ["-occurred_at"]

    def get_permissions(self):
        self.required_permission = ACT_PERMS.get(self.action, "sales.activity.read")
        return super().get_permissions()

    def get_queryset(self):
        qs = (SalesActivity.objects
              .select_related("performed_by", "lead", "customer").all())
        if self.request.user.is_superuser:
            return qs
        return _scope_by_salesperson(qs, self.request.user, "performed_by")

    def perform_create(self, serializer):
        actor = self.request.user
        emp = getattr(actor, "employee", None)
        extra = {"created_by": actor}
        if emp is not None and not serializer.validated_data.get("performed_by"):
            extra["performed_by"] = emp
        activity = serializer.save(**extra)
        record_activity(activity=activity, actor=actor, request=self.request)

    def perform_update(self, serializer):
        activity = serializer.save()
        record_audit(actor=self.request.user, action="sales.activity.updated",
                     entity_type="SalesActivity", entity_id=str(activity.pk),
                     request=self.request)


class FollowUpViewSet(viewsets.ModelViewSet):
    serializer_class = FollowUpSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "owner", "lead", "customer"]
    ordering_fields = ["due_at", "created_at"]
    ordering = ["due_at"]

    def get_permissions(self):
        self.required_permission = FU_PERMS.get(self.action, "sales.followup.read")
        return super().get_permissions()

    def get_queryset(self):
        qs = (FollowUp.objects
              .select_related("owner", "lead", "customer").all())
        if self.request.user.is_superuser:
            return qs
        return _scope_by_salesperson(qs, self.request.user, "owner")

    def perform_create(self, serializer):
        actor = self.request.user
        emp = getattr(actor, "employee", None)
        extra = {"created_by": actor}
        if emp is not None and not serializer.validated_data.get("owner"):
            extra["owner"] = emp
        fu = serializer.save(**extra)
        record_audit(actor=actor, action="followup.created",
                     entity_type="FollowUp", entity_id=str(fu.pk),
                     request=self.request)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        fu = self.get_object()
        complete_followup(followup=fu, actor=request.user, request=request)
        return Response(FollowUpSerializer(fu).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        fu = self.get_object()
        cancel_followup(followup=fu, actor=request.user, request=request)
        return Response(FollowUpSerializer(fu).data)
