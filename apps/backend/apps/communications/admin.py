from django.contrib import admin

from .models import Communication


@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "channel", "direction", "from_address",
                    "to_address", "subject")
    list_filter = ("channel", "direction")
    search_fields = ("from_address", "to_address", "subject", "body",
                     "external_ref")
