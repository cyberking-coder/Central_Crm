from django.contrib import admin

from .models import Lead, LeadAssignmentHistory, LeadStatusHistory


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("full_name", "status", "priority", "assigned_to",
                    "source", "created_at")
    list_filter = ("status", "priority", "source")
    search_fields = ("full_name", "email", "phone")
    readonly_fields = ("phone_normalised", "email_normalised",
                       "converted_customer", "converted_at",
                       "created_at", "updated_at", "created_by")


admin.site.register(LeadAssignmentHistory)
admin.site.register(LeadStatusHistory)
