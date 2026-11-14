from __future__ import annotations

from rest_framework import serializers

from .models import Expense, Invoice, InvoiceItem, Payment, Refund


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ["id", "description", "quantity", "unit_price",
                  "tax_rate", "amount"]
        read_only_fields = ["id", "amount"]


class InvoiceItemInputSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255)
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3,
                                        min_value=0.001)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2,
                                          min_value=0)
    tax_rate = serializers.DecimalField(max_digits=6, decimal_places=3,
                                        min_value=0, required=False, default=0)


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name",
                                           read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = ["id", "number", "customer", "customer_name",
                  "issued_date", "due_date",
                  "currency", "subtotal", "tax", "discount", "total",
                  "status", "notes", "items",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "number", "customer_name",
                            "subtotal", "tax", "total",
                            "status", "items",
                            "created_at", "updated_at"]


class InvoiceCreateSerializer(serializers.Serializer):
    customer = serializers.UUIDField()
    issued_date = serializers.DateField(required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    discount = serializers.DecimalField(max_digits=14, decimal_places=2,
                                         required=False, default=0, min_value=0)
    currency = serializers.CharField(max_length=3, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    items = InvoiceItemInputSerializer(many=True, min_length=1)


class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name",
                                           read_only=True)
    invoice_number = serializers.CharField(source="invoice.number",
                                           read_only=True, default=None)

    class Meta:
        model = Payment
        fields = ["id", "customer", "customer_name",
                  "invoice", "invoice_number",
                  "amount", "currency", "payment_date",
                  "method", "transaction_reference",
                  "status", "source", "notes",
                  "external_event_ref",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "customer_name", "invoice_number",
                            "source", "external_event_ref",
                            "created_at", "updated_at"]


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ["id", "payment", "amount", "currency",
                  "refunded_at", "reason", "external_ref",
                  "created_at"]
        read_only_fields = ["id", "currency", "created_at"]


class RefundCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2,
                                       min_value=0.01)
    refunded_at = serializers.DateTimeField()
    reason = serializers.CharField(required=False, allow_blank=True,
                                    max_length=255)
    external_ref = serializers.CharField(required=False, allow_blank=True,
                                          max_length=120)


class ExpenseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name",
                                             read_only=True, default=None)

    class Meta:
        model = Expense
        fields = ["id", "description", "amount", "currency",
                  "expense_date", "category",
                  "department", "department_name",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "department_name",
                            "created_at", "updated_at"]
