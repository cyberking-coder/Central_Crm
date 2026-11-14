from __future__ import annotations

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import HasPermissionCode
from apps.audit.services import record_audit
from apps.core.exports import write_csv
from apps.customers.models import Customer

from .models import Expense, Invoice, Payment
from .serializers import (
    ExpenseSerializer,
    InvoiceCreateSerializer,
    InvoiceSerializer,
    PaymentSerializer,
    RefundCreateSerializer,
    RefundSerializer,
)
from .services.invoices import create_invoice, issue_invoice, void_invoice
from .services.payments import (
    PaymentError,
    record_payment,
    record_refund,
)


INVOICE_PERMS = {
    "list": "finance.read", "retrieve": "finance.read",
    "create": "finance.manage", "update": "finance.manage",
    "partial_update": "finance.manage", "destroy": "finance.manage",
    "issue": "finance.manage", "void": "finance.manage",
    "export_csv": "finance.export",
}

PAYMENT_PERMS = {
    "list": "finance.read", "retrieve": "finance.read",
    "create": "finance.manage", "update": "finance.manage",
    "partial_update": "finance.manage", "destroy": "finance.manage",
    "refund": "finance.manage",
    "export_csv": "finance.export",
}

EXPENSE_PERMS = {
    "list": "finance.read", "retrieve": "finance.read",
    "create": "finance.manage", "update": "finance.manage",
    "partial_update": "finance.manage", "destroy": "finance.manage",
}


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter]
    filterset_fields = ["status", "customer", "currency"]
    search_fields = ["number", "customer__full_name", "notes"]
    ordering_fields = ["created_at", "issued_date", "total"]
    ordering = ["-created_at"]

    def get_permissions(self):
        self.required_permission = INVOICE_PERMS.get(
            self.action, "finance.read")
        return super().get_permissions()

    def get_queryset(self):
        return (Invoice.objects
                .select_related("customer")
                .prefetch_related("items").all())

    def create(self, request, *args, **kwargs):
        s = InvoiceCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        try:
            customer = Customer.objects.get(pk=data["customer"])
        except Customer.DoesNotExist:
            return Response({"detail": "Customer not found."},
                            status=status.HTTP_400_BAD_REQUEST)
        invoice = create_invoice(
            customer=customer, items=data["items"],
            issued_date=data.get("issued_date"),
            due_date=data.get("due_date"),
            discount=data.get("discount", 0),
            currency=data.get("currency"),
            notes=data.get("notes", ""),
            actor=request.user, request=request,
        )
        return Response(InvoiceSerializer(invoice).data,
                        status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        if instance.payments.exists():
            raise ValueError("Cannot delete an invoice with payments; void it instead.")
        record_audit(actor=self.request.user, action="invoice.deleted",
                     entity_type="Invoice", entity_id=str(instance.pk),
                     request=self.request)
        instance.delete()

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        inv = self.get_object()
        issue_invoice(invoice=inv, actor=request.user, request=request)
        return Response(InvoiceSerializer(inv).data)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        inv = self.get_object()
        try:
            void_invoice(invoice=inv, actor=request.user, request=request)
        except ValueError as e:
            return Response({"detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(InvoiceSerializer(inv).data)

    @extend_schema(responses={200: OpenApiResponse(description="CSV")})
    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())[:10_000]
        rows = [[i.number, i.customer.full_name, i.status,
                 i.currency, str(i.total),
                 i.issued_date.isoformat(),
                 i.due_date.isoformat() if i.due_date else ""]
                for i in qs]
        data = write_csv(
            ["number", "customer", "status", "currency",
             "total", "issued_date", "due_date"], rows)
        record_audit(actor=request.user, action="invoices.exported",
                     entity_type="Invoice", extra={"count": len(rows)},
                     request=request)
        resp = HttpResponse(data, content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="invoices.csv"'
        return resp


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "method", "customer", "invoice"]
    ordering_fields = ["payment_date", "created_at"]
    ordering = ["-payment_date", "-created_at"]

    def get_permissions(self):
        self.required_permission = PAYMENT_PERMS.get(
            self.action, "finance.read")
        return super().get_permissions()

    def get_queryset(self):
        return Payment.objects.select_related("customer", "invoice").all()

    def create(self, request, *args, **kwargs):
        s = PaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        try:
            p = record_payment(
                customer=data["customer"],
                invoice=data.get("invoice"),
                amount=data["amount"],
                currency=data["currency"],
                payment_date=data["payment_date"],
                method=data["method"],
                transaction_reference=data.get("transaction_reference", ""),
                status=data.get("status", Payment.Status.SUCCESSFUL),
                notes=data.get("notes", ""),
                actor=request.user, request=request,
            )
        except PaymentError as e:
            return Response({"detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentSerializer(p).data,
                        status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        record_audit(actor=self.request.user, action="payment.deleted",
                     entity_type="Payment", entity_id=str(instance.pk),
                     request=self.request)
        instance.delete()

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        payment = self.get_object()
        s = RefundCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            refund = record_refund(
                payment=payment,
                amount=s.validated_data["amount"],
                refunded_at=s.validated_data["refunded_at"],
                reason=s.validated_data.get("reason", ""),
                external_ref=s.validated_data.get("external_ref", ""),
                actor=request.user, request=request,
            )
        except PaymentError as e:
            return Response({"detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(RefundSerializer(refund).data,
                        status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: OpenApiResponse(description="CSV")})
    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())[:10_000]
        rows = [[str(p.pk), p.customer.full_name,
                 p.invoice.number if p.invoice_id else "",
                 str(p.amount), p.currency, p.status, p.method,
                 p.payment_date.isoformat(),
                 p.transaction_reference]
                for p in qs]
        data = write_csv(
            ["id", "customer", "invoice", "amount", "currency",
             "status", "method", "date", "reference"], rows)
        record_audit(actor=request.user, action="payments.exported",
                     entity_type="Payment", extra={"count": len(rows)},
                     request=request)
        resp = HttpResponse(data, content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="payments.csv"'
        return resp


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["department", "category", "currency"]
    ordering_fields = ["expense_date", "created_at", "amount"]
    ordering = ["-expense_date"]

    def get_permissions(self):
        self.required_permission = EXPENSE_PERMS.get(
            self.action, "finance.read")
        return super().get_permissions()

    def get_queryset(self):
        return Expense.objects.select_related("department").all()

    def perform_create(self, serializer):
        exp = serializer.save(recorded_by=self.request.user)
        record_audit(actor=self.request.user, action="expense.recorded",
                     entity_type="Expense", entity_id=str(exp.pk),
                     after={"amount": str(exp.amount), "currency": exp.currency},
                     request=self.request)

    def perform_update(self, serializer):
        exp = serializer.save()
        record_audit(actor=self.request.user, action="expense.updated",
                     entity_type="Expense", entity_id=str(exp.pk),
                     request=self.request)
