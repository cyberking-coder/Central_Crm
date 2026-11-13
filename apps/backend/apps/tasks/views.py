from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import HasPermissionCode
from apps.audit.services import record_audit

from .models import Task
from .serializers import TaskSerializer
from .services.tasks import complete_task, notify_task_assigned


PERMS = {
    "list": "tasks.read", "retrieve": "tasks.read",
    "create": "tasks.create",
    "update": "tasks.update", "partial_update": "tasks.update",
    "destroy": "tasks.delete",
    "complete": "tasks.update", "mine": "tasks.read",
}


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter,
                       filters.SearchFilter]
    filterset_fields = ["status", "priority", "assignee", "related_kind"]
    search_fields = ["title", "description"]
    ordering_fields = ["due_at", "created_at", "priority"]
    ordering = ["-created_at"]

    def get_permissions(self):
        self.required_permission = PERMS.get(self.action, "tasks.read")
        return super().get_permissions()

    def get_queryset(self):
        qs = Task.objects.select_related("assignee").all()
        user = self.request.user
        if user.is_superuser:
            return qs
        role = user.role.name if user.role_id else None
        if role in ("Salesperson", "Customer Support", "Webinar Manager",
                    "Finance"):
            emp = getattr(user, "employee", None)
            if emp is None:
                return qs.filter(created_by=user)
            return qs.filter(assignee=emp) | qs.filter(created_by=user)
        return qs

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user)
        record_audit(actor=self.request.user, action="task.created",
                     entity_type="Task", entity_id=str(task.pk),
                     request=self.request)
        notify_task_assigned(task)

    def perform_update(self, serializer):
        task = serializer.save()
        record_audit(actor=self.request.user, action="task.updated",
                     entity_type="Task", entity_id=str(task.pk),
                     request=self.request)

    def perform_destroy(self, instance):
        record_audit(actor=self.request.user, action="task.deleted",
                     entity_type="Task", entity_id=str(instance.pk),
                     request=self.request)
        instance.delete()

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        complete_task(task=task, actor=request.user, request=request)
        return Response(TaskSerializer(task).data)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        """Shortcut: tasks assigned to the current user's Employee."""
        emp = getattr(request.user, "employee", None)
        qs = self.filter_queryset(
            Task.objects.filter(assignee=emp) if emp is not None
            else Task.objects.none()
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(TaskSerializer(page, many=True).data)
        return Response(TaskSerializer(qs, many=True).data)
