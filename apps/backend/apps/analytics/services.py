"""
Single source of KPI formulas.

Every metric here is consumed by:
- `/api/v1/analytics/dashboard/*` endpoints
- reports (Phase 8)
- CSV exports
- the future AI assistant (Phase 10)

**Do not** inline these counts anywhere else — tests assert the dashboard
numbers reconcile with reports because both import from this module.

Each function:
- Accepts a `date` (interpreted in the company timezone).
- Converts to a half-open UTC range via `apps.core.timezones` (Part 17 #6).
- Returns a plain dict or int suitable for API serialisation.
- Applies optional employee / department / source filters.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type, datetime
from typing import Any
from uuid import UUID

from decimal import Decimal

from django.db.models import Count, Q, Sum

from apps.core.timezones import (
    company_day_range_utc,
    company_week_range_utc,
    now_company,
)
from apps.customers.models import Customer
from apps.employees.models import Employee
from apps.finance.models import Expense, Invoice, Payment, Refund
from apps.leads.models import Lead, LeadAssignmentHistory
from apps.marketing.models import LeadSource
from apps.sales.models import FollowUp, SalesActivity
from apps.tasks.models import Task


# --------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Filters:
    employee_id: UUID | None = None
    department_id: UUID | None = None
    source_id: UUID | None = None


def _apply_lead_filters(qs, f: Filters):
    if f.employee_id:
        qs = qs.filter(assigned_to_id=f.employee_id)
    if f.department_id:
        qs = qs.filter(assigned_to__department_id=f.department_id)
    if f.source_id:
        qs = qs.filter(source_id=f.source_id)
    return qs


def _apply_customer_filters(qs, f: Filters):
    if f.employee_id:
        qs = qs.filter(assigned_to_id=f.employee_id)
    if f.department_id:
        qs = qs.filter(assigned_to__department_id=f.department_id)
    if f.source_id:
        qs = qs.filter(source_id=f.source_id)
    return qs


def _apply_activity_filters(qs, f: Filters):
    if f.employee_id:
        qs = qs.filter(performed_by_id=f.employee_id)
    if f.department_id:
        qs = qs.filter(performed_by__department_id=f.department_id)
    return qs


# --------------------------------------------------------------------------
# Atomic metrics
# --------------------------------------------------------------------------

def leads_created_in_range(start: datetime, end: datetime,
                           f: Filters = Filters()) -> int:
    """Count of leads where created_at ∈ [start, end)."""
    qs = Lead.objects.filter(created_at__gte=start, created_at__lt=end)
    return _apply_lead_filters(qs, f).count()


def leads_assigned_in_range(start: datetime, end: datetime,
                            f: Filters = Filters()) -> int:
    """Count of assignment EVENTS in the range (not current state)."""
    qs = LeadAssignmentHistory.objects.filter(
        assigned_at__gte=start, assigned_at__lt=end)
    if f.employee_id:
        qs = qs.filter(to_employee_id=f.employee_id)
    if f.department_id:
        qs = qs.filter(to_employee__department_id=f.department_id)
    return qs.count()


def leads_unassigned_now(f: Filters = Filters()) -> int:
    """Open leads with no assignee right now."""
    qs = Lead.objects.filter(
        assigned_to__isnull=True,
        status__in=[Lead.Status.NEW, Lead.Status.UNASSIGNED],
    )
    if f.source_id:
        qs = qs.filter(source_id=f.source_id)
    return qs.count()


def customers_converted_in_range(start: datetime, end: datetime,
                                 f: Filters = Filters()) -> int:
    qs = Lead.objects.filter(
        converted_at__isnull=False,
        converted_at__gte=start, converted_at__lt=end,
    )
    return _apply_lead_filters(qs, f).count()


def activities_in_range(start: datetime, end: datetime,
                        f: Filters = Filters(),
                        kind: str | None = None) -> int:
    qs = SalesActivity.objects.filter(
        occurred_at__gte=start, occurred_at__lt=end)
    if kind:
        qs = qs.filter(kind=kind)
    return _apply_activity_filters(qs, f).count()


def followups_due_in_range(start: datetime, end: datetime,
                           f: Filters = Filters()) -> int:
    qs = FollowUp.objects.filter(
        status=FollowUp.Status.OPEN,
        due_at__gte=start, due_at__lt=end,
    )
    if f.employee_id:
        qs = qs.filter(owner_id=f.employee_id)
    if f.department_id:
        qs = qs.filter(owner__department_id=f.department_id)
    return qs.count()


def followups_overdue_now(f: Filters = Filters()) -> int:
    now = now_company()
    qs = FollowUp.objects.filter(
        status=FollowUp.Status.OPEN, due_at__lt=now)
    if f.employee_id:
        qs = qs.filter(owner_id=f.employee_id)
    if f.department_id:
        qs = qs.filter(owner__department_id=f.department_id)
    return qs.count()


def tasks_overdue_now(f: Filters = Filters()) -> int:
    now = now_company()
    qs = Task.objects.filter(
        status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS],
        due_at__lt=now,
    )
    if f.employee_id:
        qs = qs.filter(assignee_id=f.employee_id)
    if f.department_id:
        qs = qs.filter(assignee__department_id=f.department_id)
    return qs.count()


def tasks_completed_in_range(start: datetime, end: datetime,
                             f: Filters = Filters()) -> int:
    qs = Task.objects.filter(
        status=Task.Status.COMPLETED,
        completed_at__isnull=False,
        completed_at__gte=start, completed_at__lt=end,
    )
    if f.employee_id:
        qs = qs.filter(assignee_id=f.employee_id)
    if f.department_id:
        qs = qs.filter(assignee__department_id=f.department_id)
    return qs.count()


# --------------------------------------------------------------------------
# Composite payloads
# --------------------------------------------------------------------------

def today_payload(d: date_type | None = None,
                  f: Filters = Filters()) -> dict[str, Any]:
    """KPI card payload for the given company-local day (default: today)."""
    if d is None:
        d = now_company().date()
    start, end = company_day_range_utc(d)

    return {
        "date": d.isoformat(),
        "leads_received": leads_created_in_range(start, end, f),
        "leads_assigned": leads_assigned_in_range(start, end, f),
        "leads_awaiting_assignment": leads_unassigned_now(f),
        "calls_logged": activities_in_range(
            start, end, f, kind=SalesActivity.Kind.CALL_OUT) +
            activities_in_range(start, end, f, kind=SalesActivity.Kind.CALL_IN),
        "activities_logged": activities_in_range(start, end, f),
        "followups_due_today": followups_due_in_range(start, end, f),
        "followups_overdue": followups_overdue_now(f),
        "customers_converted": customers_converted_in_range(start, end, f),
        "tasks_overdue": tasks_overdue_now(f),
        "tasks_completed": tasks_completed_in_range(start, end, f),
        # Finance (strings — Decimals aren't JSON-native)
        "gross_collections": str(gross_collections_in_range(start, end)),
        "refunds": str(refunds_in_range(start, end)),
        "net_collections": str(net_collections_in_range(start, end)),
        "outstanding_invoices": str(outstanding_invoice_total()),
        "pending_payments": str(pending_payment_total()),
    }


def weekly_payload(d: date_type | None = None,
                   f: Filters = Filters()) -> dict[str, Any]:
    """KPI card payload for the Monday-start week containing `d`."""
    if d is None:
        d = now_company().date()
    start, end = company_week_range_utc(d)
    return {
        "week_start": start.date().isoformat(),
        "week_end": (end.date()).isoformat(),
        "leads_received": leads_created_in_range(start, end, f),
        "leads_assigned": leads_assigned_in_range(start, end, f),
        "customers_converted": customers_converted_in_range(start, end, f),
        "activities_logged": activities_in_range(start, end, f),
        "tasks_completed": tasks_completed_in_range(start, end, f),
        "leads_by_source": leads_by_source_in_range(start, end, f),
        "gross_collections": str(gross_collections_in_range(start, end)),
        "refunds": str(refunds_in_range(start, end)),
        "net_collections": str(net_collections_in_range(start, end)),
        "expenses": str(expenses_in_range(start, end)),
    }


def leads_by_source_in_range(start: datetime, end: datetime,
                             f: Filters = Filters()) -> list[dict[str, Any]]:
    qs = Lead.objects.filter(created_at__gte=start, created_at__lt=end)
    qs = _apply_lead_filters(qs, f)
    rows = (qs.values("source__name", "source_id")
            .annotate(count=Count("id"))
            .order_by("-count"))
    return [
        {"source_id": str(r["source_id"]) if r["source_id"] else None,
         "source": r["source__name"] or "—",
         "count": r["count"]}
        for r in rows
    ]


# --------------------------------------------------------------------------
# Finance metrics (Part 17 #2 — the single source of truth)
# --------------------------------------------------------------------------

ZERO = Decimal("0.00")


def gross_collections_in_range(start: datetime, end: datetime) -> Decimal:
    """Sum of SUCCESSFUL payment amounts recorded in the range."""
    agg = Payment.objects.filter(
        status=Payment.Status.SUCCESSFUL,
        payment_date__gte=start.date(), payment_date__lt=end.date(),
    ).aggregate(s=Sum("amount"))
    return agg["s"] or ZERO


def refunds_in_range(start: datetime, end: datetime) -> Decimal:
    agg = Refund.objects.filter(
        refunded_at__gte=start, refunded_at__lt=end,
    ).aggregate(s=Sum("amount"))
    return agg["s"] or ZERO


def net_collections_in_range(start: datetime, end: datetime) -> Decimal:
    return gross_collections_in_range(start, end) - refunds_in_range(start, end)


def outstanding_invoice_total() -> Decimal:
    """Sum of totals for invoices still issued or partially paid.
    Not range-based — reflects the current balance sheet."""
    agg = Invoice.objects.filter(
        status__in=[Invoice.Status.ISSUED, Invoice.Status.PARTIALLY_PAID],
    ).aggregate(s=Sum("total"))
    return agg["s"] or ZERO


def pending_payment_total() -> Decimal:
    agg = Payment.objects.filter(status=Payment.Status.PENDING).aggregate(
        s=Sum("amount"))
    return agg["s"] or ZERO


def expenses_in_range(start: datetime, end: datetime) -> Decimal:
    agg = Expense.objects.filter(
        expense_date__gte=start.date(), expense_date__lt=end.date(),
    ).aggregate(s=Sum("amount"))
    return agg["s"] or ZERO


def salesperson_leaderboard(start: datetime, end: datetime,
                            limit: int = 10) -> list[dict[str, Any]]:
    """Activity count + converted customers per employee in the range."""
    activity_agg = dict(
        SalesActivity.objects
        .filter(occurred_at__gte=start, occurred_at__lt=end,
                performed_by__isnull=False)
        .values("performed_by_id")
        .annotate(n=Count("id"))
        .values_list("performed_by_id", "n")
    )
    conv_agg = dict(
        Lead.objects
        .filter(converted_at__isnull=False,
                converted_at__gte=start, converted_at__lt=end,
                assigned_to__isnull=False)
        .values("assigned_to_id")
        .annotate(n=Count("id"))
        .values_list("assigned_to_id", "n")
    )
    emp_ids = set(activity_agg) | set(conv_agg)
    employees = Employee.objects.filter(id__in=emp_ids).only(
        "id", "full_name", "department_id")
    rows = [
        {
            "employee_id": str(e.id),
            "employee_name": e.full_name,
            "activities": activity_agg.get(e.id, 0),
            "conversions": conv_agg.get(e.id, 0),
        }
        for e in employees
    ]
    rows.sort(key=lambda r: (-r["activities"], -r["conversions"]))
    return rows[:limit]
