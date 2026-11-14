from django.contrib import admin

from .models import (
    Expense,
    Invoice,
    InvoiceItem,
    InvoiceSequence,
    Payment,
    Refund,
    WebhookEvent,
)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "status", "currency", "total",
                    "issued_date")
    list_filter = ("status", "currency")
    search_fields = ("number", "customer__full_name")
    inlines = [InvoiceItemInline]
    readonly_fields = ("number", "subtotal", "tax", "total",
                       "created_at", "updated_at", "created_by")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("customer", "invoice", "amount", "currency", "status",
                    "method", "payment_date")
    list_filter = ("status", "method", "source")
    search_fields = ("customer__full_name", "transaction_reference")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("payment", "amount", "currency", "refunded_at")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "currency", "expense_date",
                    "department")
    list_filter = ("category", "department")
    search_fields = ("description",)


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "provider_event_id", "status",
                    "received_at", "processed_at")
    list_filter = ("provider", "status")
    search_fields = ("provider_event_id",)
    readonly_fields = tuple(f.name for f in WebhookEvent._meta.fields)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(InvoiceSequence)
