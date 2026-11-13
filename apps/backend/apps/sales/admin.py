from django.contrib import admin

from .models import FollowUp, SalesActivity


@admin.register(SalesActivity)
class SalesActivityAdmin(admin.ModelAdmin):
    list_display = ("kind", "performed_by", "lead", "customer", "occurred_at")
    list_filter = ("kind",)
    search_fields = ("outcome", "discussion_summary")


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("summary", "owner", "due_at", "status")
    list_filter = ("status",)
    search_fields = ("summary",)
