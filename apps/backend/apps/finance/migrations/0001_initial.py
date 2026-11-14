import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customers", "0001_initial"),
        ("departments", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InvoiceSequence",
            fields=[
                ("year", models.PositiveIntegerField(primary_key=True,
                                                     serialize=False)),
                ("last_number", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("number", models.CharField(max_length=24, unique=True)),
                ("issued_date", models.DateField()),
                ("due_date", models.DateField(blank=True, null=True)),
                ("currency", models.CharField(max_length=3)),
                ("subtotal", models.DecimalField(max_digits=14, decimal_places=2,
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("tax", models.DecimalField(max_digits=14, decimal_places=2,
                    default=0,
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("discount", models.DecimalField(max_digits=14, decimal_places=2,
                    default=0,
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("total", models.DecimalField(max_digits=14, decimal_places=2,
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("status", models.CharField(
                    choices=[("draft", "Draft"), ("issued", "Issued"),
                             ("partially_paid", "Partially paid"),
                             ("paid", "Paid"), ("void", "Void")],
                    db_index=True, default="draft", max_length=16)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_invoices",
                    to=settings.AUTH_USER_MODEL)),
                ("customer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="invoices", to="customers.customer")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["customer", "status"],
                               name="inv_customer_status_idx"),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["status", "issued_date"],
                               name="inv_status_date_idx"),
        ),
        migrations.CreateModel(
            name="InvoiceItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("description", models.CharField(max_length=255)),
                ("quantity", models.DecimalField(max_digits=14, decimal_places=3,
                    validators=[django.core.validators.MinValueValidator(0.001)])),
                ("unit_price", models.DecimalField(max_digits=14, decimal_places=2,
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("tax_rate", models.DecimalField(max_digits=6, decimal_places=3,
                    default=0, help_text="Percent, e.g. 18.000 for 18%.",
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("amount", models.DecimalField(max_digits=14, decimal_places=2,
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("invoice", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="items", to="finance.invoice")),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("amount", models.DecimalField(max_digits=14, decimal_places=2,
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("currency", models.CharField(max_length=3)),
                ("payment_date", models.DateField(db_index=True)),
                ("method", models.CharField(
                    choices=[("cash", "Cash"),
                             ("bank_transfer", "Bank transfer"),
                             ("upi", "UPI"), ("card", "Card"),
                             ("gateway", "Payment gateway"),
                             ("other", "Other")],
                    default="other", max_length=24)),
                ("transaction_reference", models.CharField(
                    blank=True, db_index=True, max_length=120)),
                ("status", models.CharField(
                    choices=[("pending", "Pending"),
                             ("successful", "Successful"),
                             ("failed", "Failed"),
                             ("refunded", "Refunded"),
                             ("partially_refunded", "Partially refunded")],
                    db_index=True, default="successful", max_length=24)),
                ("source", models.CharField(
                    choices=[("manual", "Manual"),
                             ("gateway", "Gateway webhook"),
                             ("import", "Imported")],
                    default="manual", max_length=12)),
                ("notes", models.TextField(blank=True)),
                ("external_event_ref", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="payments", to="customers.customer")),
                ("invoice", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="payments", to="finance.invoice")),
                ("recorded_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="recorded_payments",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-payment_date", "-created_at"]},
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["status", "payment_date"],
                               name="pay_status_date_idx"),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["customer", "-payment_date"],
                               name="pay_customer_date_idx"),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.UniqueConstraint(
                condition=models.Q(("transaction_reference", ""), _negated=True),
                fields=("method", "transaction_reference"),
                name="payment_unique_method_reference",
            ),
        ),
        migrations.CreateModel(
            name="Refund",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("amount", models.DecimalField(max_digits=14, decimal_places=2,
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("currency", models.CharField(max_length=3)),
                ("refunded_at", models.DateTimeField()),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("external_ref", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("payment", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="refunds", to="finance.payment")),
                ("recorded_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="recorded_refunds",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-refunded_at"]},
        ),
        migrations.AddIndex(
            model_name="refund",
            index=models.Index(fields=["refunded_at"],
                               name="refund_date_idx"),
        ),
        migrations.CreateModel(
            name="Expense",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("description", models.CharField(max_length=255)),
                ("amount", models.DecimalField(max_digits=14, decimal_places=2,
                    validators=[django.core.validators.MinValueValidator(0)])),
                ("currency", models.CharField(max_length=3)),
                ("expense_date", models.DateField(db_index=True)),
                ("category", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("department", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="expenses",
                    to="departments.department")),
                ("recorded_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="recorded_expenses",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-expense_date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="WebhookEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("provider", models.CharField(max_length=40)),
                ("provider_event_id", models.CharField(max_length=120)),
                ("event_type", models.CharField(blank=True, max_length=80)),
                ("payload_hash", models.CharField(blank=True, max_length=64)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(
                    choices=[("received", "Received"),
                             ("processed", "Processed"),
                             ("failed", "Failed")],
                    default="received", max_length=16)),
                ("error", models.TextField(blank=True)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="webhookevent",
            constraint=models.UniqueConstraint(
                fields=("provider", "provider_event_id"),
                name="webhook_provider_event_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="webhookevent",
            index=models.Index(fields=["provider", "status"],
                               name="webhook_provider_status_idx"),
        ),
    ]
