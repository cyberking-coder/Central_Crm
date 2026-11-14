from django.contrib import admin

from .models import Webinar, WebinarAttendance, WebinarRegistration


@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    list_display = ("title", "start_at", "status", "registration_limit", "host")
    list_filter = ("status",)
    search_fields = ("title",)


@admin.register(WebinarRegistration)
class WebinarRegistrationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "webinar", "email", "status", "created_at")
    list_filter = ("status", "webinar")
    search_fields = ("full_name", "email", "phone")


@admin.register(WebinarAttendance)
class WebinarAttendanceAdmin(admin.ModelAdmin):
    list_display = ("registration", "status", "joined_at", "duration_minutes")
    list_filter = ("status",)
