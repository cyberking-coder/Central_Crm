from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.customers.models import Customer

from ..models import Invoice, InvoiceItem, InvoiceSequence, ZERO


def _q(d: Decimal | int | float | str) -> Decimal:
    """Quantise to 2 decimal places with banker-safe rounding."""
    return Decimal(d).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@transaction.atomic
def _next_invoice_number(year: int) -> str:
    row, _ = InvoiceSequence.objects.select_for_update().get_or_create(
        year=year)
    row.last_number += 1
    row.save(update_fields=["last_number"])
    return f"INV-{year}-{row.last_number:05d}"


@transaction.atomic
def create_invoice(*, customer: Customer, items: Iterable[dict],
                   issued_date=None, due_date=None,
                   discount: Decimal | str | int = 0,
                   currency: str | None = None,
                   notes: str = "",
                   actor=None, request=None) -> Invoice:
    """
    Create an invoice from a list of item dicts:
        [{description, quantity, unit_price, tax_rate?}, ...]

    Server computes line amounts and the totals; clients can't forge them.
    """
    issued = issued_date or timezone.now().date()
    currency = currency or settings.COMPANY_DEFAULT_CURRENCY

    subtotal = Decimal("0.00")
    tax_total = Decimal("0.00")
    staged_items = []
    for raw in items:
        qty = Decimal(str(raw["quantity"]))
        price = Decimal(str(raw["unit_price"]))
        tax_rate = Decimal(str(raw.get("tax_rate", 0)))
        line_net = _q(qty * price)
        line_tax = _q(line_net * tax_rate / Decimal("100"))
        subtotal += line_net
        tax_total += line_tax
        staged_items.append({
            "description": raw["description"],
            "quantity": qty,
            "unit_price": _q(price),
            "tax_rate": tax_rate,
            "amount": line_net,
        })

    discount_d = _q(discount)
    total = _q(subtotal + tax_total - discount_d)
    if total < ZERO:
        total = ZERO

    invoice = Invoice.objects.create(
        number=_next_invoice_number(issued.year),
        customer=customer,
        issued_date=issued, due_date=due_date,
        currency=currency,
        subtotal=_q(subtotal), tax=_q(tax_total), discount=discount_d,
        total=total,
        status=Invoice.Status.DRAFT,
        notes=notes,
        created_by=actor if getattr(actor, "is_authenticated", False) else None,
    )
    InvoiceItem.objects.bulk_create([
        InvoiceItem(invoice=invoice, **row) for row in staged_items
    ])

    record_audit(
        actor=actor, action="invoice.created",
        entity_type="Invoice", entity_id=str(invoice.pk),
        after={"total": str(invoice.total), "currency": invoice.currency},
        request=request,
    )
    return invoice


@transaction.atomic
def issue_invoice(*, invoice: Invoice, actor=None, request=None) -> Invoice:
    if invoice.status != Invoice.Status.DRAFT:
        return invoice
    invoice.status = Invoice.Status.ISSUED
    invoice.save(update_fields=["status", "updated_at"])
    record_audit(actor=actor, action="invoice.issued",
                 entity_type="Invoice", entity_id=str(invoice.pk),
                 request=request)
    return invoice


@transaction.atomic
def void_invoice(*, invoice: Invoice, actor=None, request=None) -> Invoice:
    # Voiding does not delete payments — they remain against a customer.
    if invoice.status == Invoice.Status.PAID:
        raise ValueError("Paid invoices cannot be voided.")
    invoice.status = Invoice.Status.VOID
    invoice.save(update_fields=["status", "updated_at"])
    record_audit(actor=actor, action="invoice.voided",
                 entity_type="Invoice", entity_id=str(invoice.pk),
                 request=request)
    return invoice


def paid_amount(invoice: Invoice) -> Decimal:
    """Sum of successful payments against this invoice (post-refund)."""
    from ..models import Payment
    rows = Payment.objects.filter(
        invoice=invoice, status=Payment.Status.SUCCESSFUL,
    ).values_list("id", "amount")
    total = Decimal("0.00")
    for pid, amt in rows:
        refunded = sum(
            (r.amount for r in
             invoice.payments.get(pk=pid).refunds.all()),  # type: ignore[attr-defined]
            Decimal("0.00"),
        )
        total += (Decimal(amt) - refunded)
    return total


def recompute_invoice_status(invoice: Invoice) -> Invoice:
    """
    Recompute status from the ledger. Called after each payment / refund.
    Never promotes a VOID or DRAFT invoice.
    """
    if invoice.status in (Invoice.Status.VOID, Invoice.Status.DRAFT):
        return invoice
    paid = paid_amount(invoice)
    if paid <= ZERO:
        new = Invoice.Status.ISSUED
    elif paid < invoice.total:
        new = Invoice.Status.PARTIALLY_PAID
    else:
        new = Invoice.Status.PAID
    if new != invoice.status:
        invoice.status = new
        invoice.save(update_fields=["status", "updated_at"])
    return invoice
