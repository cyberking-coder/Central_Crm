from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.audit.services import record_audit
from apps.integrations.outbound import fire_event

from ..models import Invoice, Payment, Refund
from .invoices import recompute_invoice_status


ZERO = Decimal("0.00")


class PaymentError(Exception):
    pass


@transaction.atomic
def record_payment(*, customer, invoice=None, amount, currency,
                   payment_date, method: str,
                   transaction_reference: str = "",
                   status: str = Payment.Status.SUCCESSFUL,
                   source: str = Payment.Source.MANUAL,
                   external_event_ref: str = "",
                   notes: str = "",
                   actor=None, request=None) -> Payment:
    amount_d = Decimal(str(amount))
    if amount_d <= ZERO:
        raise PaymentError("Payment amount must be positive.")

    if invoice is not None and invoice.currency != currency:
        raise PaymentError(
            f"Currency {currency} does not match invoice currency {invoice.currency}.")

    try:
        p = Payment.objects.create(
            customer=customer, invoice=invoice,
            amount=amount_d, currency=currency,
            payment_date=payment_date, method=method,
            transaction_reference=transaction_reference,
            status=status, source=source,
            external_event_ref=external_event_ref,
            notes=notes,
            recorded_by=actor if getattr(actor, "is_authenticated", False) else None,
        )
    except IntegrityError as exc:
        # The (method, transaction_reference) unique constraint fired.
        raise PaymentError(
            "A payment with this transaction reference already exists.") from exc

    record_audit(
        actor=actor, action="payment.recorded",
        entity_type="Payment", entity_id=str(p.pk),
        after={"amount": str(p.amount), "currency": p.currency,
               "status": p.status, "source": p.source},
        request=request,
    )

    if invoice is not None and p.status == Payment.Status.SUCCESSFUL:
        before_status = invoice.status
        recompute_invoice_status(invoice)
        if invoice.status == Invoice.Status.PAID and before_status != Invoice.Status.PAID:
            fire_event("invoice.paid", {
                "invoice_id": str(invoice.pk),
                "number": invoice.number,
                "customer_id": str(invoice.customer_id),
                "total": str(invoice.total),
                "currency": invoice.currency,
            })
    if p.status == Payment.Status.SUCCESSFUL:
        fire_event("payment.successful", {
            "payment_id": str(p.pk),
            "customer_id": str(p.customer_id),
            "amount": str(p.amount),
            "currency": p.currency,
            "invoice_id": str(p.invoice_id) if p.invoice_id else None,
        })
    return p


@transaction.atomic
def record_refund(*, payment: Payment, amount, refunded_at,
                  reason: str = "", external_ref: str = "",
                  actor=None, request=None) -> Refund:
    amount_d = Decimal(str(amount))
    if amount_d <= ZERO:
        raise PaymentError("Refund amount must be positive.")
    if payment.status not in (Payment.Status.SUCCESSFUL,
                              Payment.Status.PARTIALLY_REFUNDED):
        raise PaymentError("Only successful payments can be refunded.")

    already = sum((r.amount for r in payment.refunds.all()), ZERO)
    remaining = payment.amount - already
    if amount_d > remaining:
        raise PaymentError(
            f"Refund exceeds remaining payment balance ({remaining}).")

    refund = Refund.objects.create(
        payment=payment, amount=amount_d, currency=payment.currency,
        refunded_at=refunded_at, reason=reason, external_ref=external_ref,
        recorded_by=actor if getattr(actor, "is_authenticated", False) else None,
    )

    # Update payment status.
    new_total = already + amount_d
    if new_total >= payment.amount:
        payment.status = Payment.Status.REFUNDED
    else:
        payment.status = Payment.Status.PARTIALLY_REFUNDED
    payment.save(update_fields=["status", "updated_at"])

    record_audit(
        actor=actor, action="payment.refunded",
        entity_type="Payment", entity_id=str(payment.pk),
        after={"refund_id": str(refund.pk), "amount": str(refund.amount)},
        request=request,
    )

    if payment.invoice_id:
        recompute_invoice_status(payment.invoice)
    fire_event("payment.refunded", {
        "refund_id": str(refund.pk),
        "payment_id": str(payment.pk),
        "amount": str(refund.amount),
        "currency": refund.currency,
    })
    return refund
