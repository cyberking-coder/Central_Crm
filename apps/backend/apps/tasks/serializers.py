from __future__ import annotations

from rest_framework import serializers

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source="assignee.full_name",
                                           read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "description",
                  "assignee", "assignee_name",
                  "due_at", "priority", "status",
                  "related_kind", "related_id",
                  "is_overdue", "completed_at",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "assignee_name", "is_overdue",
                            "completed_at", "created_at", "updated_at"]
