from django.contrib import admin

from .models import Customer, CustomerTimelineEvent


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "status", "assigned_to", "source", "created_at")
    list_filter = ("status", "source")
    search_fields = ("full_name", "email", "phone")
    readonly_fields = ("phone_normalised", "email_normalised",
                       "created_at", "updated_at", "created_by")


admin.site.register(CustomerTimelineEvent)
