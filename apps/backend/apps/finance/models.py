"""
Finance models.

Design notes (Part 17 #2):
- Every monetary column is Decimal(max_digits=14, decimal_places=2).
  Enough for 999,999,999,999.99 which covers any realistic CRM.
- Currency is a 3-letter ISO code stored explicitly on every money row,
  never inferred. Mixed-currency rollups are the service layer's problem,
  not the model's.
- No cascade delete from Payment / Refund / Invoice through finance:
  on_delete=PROTECT everywhere so a bad delete attempt raises instead of
  silently destroying ledger rows.
- Status transitions are enforced in services, not in model .save().
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

ZERO = Decimal("0.00")


class InvoiceSequence(models.Model):
    """Per-year counter used to generate `INV-YYYY-00001`."""
    year = models.PositiveIntegerField(primary_key=True)
    last_number = models.PositiveIntegerField(default=0)


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PARTIALLY_PAID = "partially_paid", "Partially paid"
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=24, unique=True)
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.PROTECT,
        related_name="invoices",
    )
    issued_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)

    currency = models.CharField(max_length=3)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2,
                                   validators=[MinValueValidator(ZERO)])
    tax = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO,
                              validators=[MinValueValidator(ZERO)])
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO,
                                   validators=[MinValueValidator(ZERO)])
    total = models.DecimalField(max_digits=14, decimal_places=2,
                                validators=[MinValueValidator(ZERO)])

    status = models.CharField(max_length=16, choices=Status.choices,
                              default=Status.DRAFT, db_index=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_invoices",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["status", "issued_date"]),
        ]


class InvoiceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                                related_name="items")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=14, decimal_places=3,
                                   validators=[MinValueValidator(Decimal("0.001"))])
    unit_price = models.DecimalField(max_digits=14, decimal_places=2,
                                     validators=[MinValueValidator(ZERO)])
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=ZERO,
                                   help_text="Percent, e.g. 18.000 for 18%.",
                                   validators=[MinValueValidator(ZERO)])
    amount = models.DecimalField(max_digits=14, decimal_places=2,
                                 validators=[MinValueValidator(ZERO)])


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank_transfer", "Bank transfer"
        UPI = "upi", "UPI"
        CARD = "card", "Card"
        GATEWAY = "gateway", "Payment gateway"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESSFUL = "successful", "Successful"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially refunded"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        GATEWAY = "gateway", "Gateway webhook"
        IMPORT = "import", "Imported"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.PROTECT,
        related_name="payments",
    )
    invoice = models.ForeignKey(
        Invoice, null=True, blank=True, on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2,
                                 validators=[MinValueValidator(ZERO)])
    currency = models.CharField(max_length=3)
    payment_date = models.DateField(db_index=True)
    method = models.CharField(max_length=24, choices=Method.choices,
                              default=Method.OTHER)
    transaction_reference = models.CharField(max_length=120, blank=True,
                                              db_index=True)
    status = models.CharField(max_length=24, choices=Status.choices,
                              default=Status.SUCCESSFUL, db_index=True)
    source = models.CharField(max_length=12, choices=Source.choices,
                              default=Source.MANUAL)
    notes = models.TextField(blank=True)

    external_event_ref = models.CharField(max_length=64, blank=True)

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="recorded_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]
        indexes = [
            models.Index(fields=["status", "payment_date"]),
            models.Index(fields=["customer", "-payment_date"]),
        ]
        constraints = [
            # Reference is unique per (method, reference) when non-empty, so
            # the same bank wire can't be recorded twice.
            models.UniqueConstraint(
                fields=["method", "transaction_reference"],
                condition=~models.Q(transaction_reference=""),
                name="payment_unique_method_reference",
            ),
        ]


class Refund(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, related_name="refunds",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2,
                                 validators=[MinValueValidator(ZERO)])
    currency = models.CharField(max_length=3)
    refunded_at = models.DateTimeField()
    reason = models.CharField(max_length=255, blank=True)
    external_ref = models.CharField(max_length=120, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="recorded_refunds",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-refunded_at"]
        indexes = [models.Index(fields=["refunded_at"])]


class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2,
                                 validators=[MinValueValidator(ZERO)])
    currency = models.CharField(max_length=3)
    expense_date = models.DateField(db_index=True)
    category = models.CharField(max_length=64, blank=True)
    department = models.ForeignKey(
        "departments.Department", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="expenses",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="recorded_expenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-expense_date", "-created_at"]


class WebhookEvent(models.Model):
    """Part 17 #4: idempotency store for inbound provider webhooks."""
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=40)
    provider_event_id = models.CharField(max_length=120)
    event_type = models.CharField(max_length=80, blank=True)
    payload_hash = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices,
                              default=Status.RECEIVED)
    error = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_event_id"],
                name="webhook_provider_event_uniq",
            ),
        ]
        indexes = [models.Index(fields=["provider", "status"])]
