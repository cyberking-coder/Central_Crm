from django.contrib import admin

from .models import Campaign, LeadSource


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "source", "is_active", "start_date", "end_date")
    list_filter = ("source", "is_active")
    search_fields = ("name", "utm_campaign")
