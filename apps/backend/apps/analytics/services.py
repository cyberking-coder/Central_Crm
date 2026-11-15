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


def leads_per_day(start: datetime, end: datetime) -> list[dict[str, Any]]:
    """[{date, count}] — one row per day in [start, end)."""
    from django.db.models.functions import TruncDate
    rows = (Lead.objects
            .filter(created_at__gte=start, created_at__lt=end)
            .annotate(d=TruncDate("created_at"))
            .values("d").annotate(count=Count("id")).order_by("d"))
    return [{"date": r["d"].isoformat(), "count": r["count"]} for r in rows]


def collections_per_day(start: datetime, end: datetime) -> list[dict[str, Any]]:
    """[{date, gross, refunds, net}] from successful payments / refunds."""
    from django.db.models.functions import TruncDate
    pay_rows = (Payment.objects
                .filter(status=Payment.Status.SUCCESSFUL,
                        payment_date__gte=start.date(),
                        payment_date__lt=end.date())
                .values("payment_date")
                .annotate(gross=Sum("amount")))
    pay_map = {r["payment_date"].isoformat(): r["gross"] or ZERO
               for r in pay_rows}
    ref_rows = (Refund.objects
                .filter(refunded_at__gte=start, refunded_at__lt=end)
                .annotate(d=TruncDate("refunded_at"))
                .values("d").annotate(refunds=Sum("amount")))
    ref_map = {r["d"].isoformat(): r["refunds"] or ZERO
               for r in ref_rows}
    days = sorted(set(pay_map) | set(ref_map))
    return [
        {"date": d,
         "gross": str(pay_map.get(d, ZERO)),
         "refunds": str(ref_map.get(d, ZERO)),
         "net": str((pay_map.get(d, ZERO)) - (ref_map.get(d, ZERO)))}
        for d in days
    ]


def expenses_in_range(start: datetime, end: datetime) -> Decimal:
    agg = Expense.objects.filter(
        expense_date__gte=start.date(), expense_date__lt=end.date(),
    ).aggregate(s=Sum("amount"))
    return agg["s"] or ZERO


# --------------------------------------------------------------------------
# Reports (Phase 8) — all read from the same underlying tables. Every
# figure here is produced by a single function; CSV exports and future AI
# summaries call the same code path.
# --------------------------------------------------------------------------

def source_performance_report(start: datetime, end: datetime
                              ) -> list[dict[str, Any]]:
    """
    Per lead-source rollup over the range:
      leads, qualified, converted, conversion %, attributed_revenue.
    Attribution rule (documented): a payment contributes to a source if
    it belongs to a customer whose source matches. This is the simplest
    first-touch rule; multi-touch attribution is out of scope.
    """
    # Lead counts.
    lead_rows = (Lead.objects
                 .filter(created_at__gte=start, created_at__lt=end)
                 .values("source_id", "source__name")
                 .annotate(leads=Count("id"),
                           qualified=Count("id", filter=Q(status__in=[
                               Lead.Status.QUALIFIED,
                               Lead.Status.CONVERTED,
                           ])),
                           converted=Count("id", filter=Q(
                               status=Lead.Status.CONVERTED))))

    # Attributed revenue from customers who match each source.
    revenue_rows = dict(Payment.objects.filter(
        status=Payment.Status.SUCCESSFUL,
        payment_date__gte=start.date(), payment_date__lt=end.date(),
        customer__source__isnull=False,
    ).values("customer__source_id").annotate(s=Sum("amount"))
    .values_list("customer__source_id", "s"))

    out = []
    for row in lead_rows:
        leads = row["leads"] or 0
        converted = row["converted"] or 0
        conv_pct = (converted / leads * 100.0) if leads else 0.0
        out.append({
            "source_id": str(row["source_id"]) if row["source_id"] else None,
            "source": row["source__name"] or "—",
            "leads": leads,
            "qualified": row["qualified"] or 0,
            "converted": converted,
            "conversion_pct": round(conv_pct, 1),
            "attributed_revenue": str(
                revenue_rows.get(row["source_id"], ZERO)),
        })
    return sorted(out, key=lambda r: -r["leads"])


def campaign_performance_report(start: datetime, end: datetime
                                ) -> list[dict[str, Any]]:
    """
    Per-campaign leads / converted / revenue; shows CPL + ROI when spend
    is present. Revenue attribution: payments by customers converted from
    leads of this campaign in the range.
    """
    from apps.marketing.models import Campaign

    lead_rows = (Lead.objects
                 .filter(created_at__gte=start, created_at__lt=end,
                         campaign__isnull=False)
                 .values("campaign_id")
                 .annotate(leads=Count("id"),
                           converted=Count("id", filter=Q(
                               status=Lead.Status.CONVERTED))))
    leads_by_campaign = {r["campaign_id"]: r for r in lead_rows}

    # Revenue: payments on customers who came from leads of this campaign.
    rev_rows = dict(Payment.objects.filter(
        status=Payment.Status.SUCCESSFUL,
        payment_date__gte=start.date(), payment_date__lt=end.date(),
    ).filter(customer__source_leads__campaign__isnull=False).values(
        "customer__source_leads__campaign_id",
    ).annotate(s=Sum("amount")).values_list(
        "customer__source_leads__campaign_id", "s"))

    out = []
    for c in Campaign.objects.select_related("source").all():
        entry = leads_by_campaign.get(c.id, {"leads": 0, "converted": 0})
        leads = entry["leads"] or 0
        revenue = rev_rows.get(c.id, ZERO) or ZERO
        spend = c.spend or ZERO
        cpl = (spend / leads) if leads and spend else None
        roi_pct = ((revenue - spend) / spend * 100) if spend else None
        out.append({
            "campaign_id": str(c.id),
            "campaign": c.name,
            "source": c.source.name if c.source_id else "—",
            "leads": leads,
            "converted": entry["converted"] or 0,
            "spend": str(spend),
            "attributed_revenue": str(revenue),
            "cost_per_lead": str(cpl.quantize(Decimal("0.01"))) if cpl else None,
            "roi_pct": float(roi_pct.quantize(Decimal("0.1"))) if roi_pct is not None else None,
        })
    return sorted(out, key=lambda r: -r["leads"])


def conversion_funnel(start: datetime, end: datetime) -> dict[str, int]:
    """How many leads created in [start, end) reached each stage."""
    in_range = Lead.objects.filter(created_at__gte=start, created_at__lt=end)
    return {
        "leads": in_range.count(),
        "contacted": in_range.filter(status__in=[
            Lead.Status.CONTACTED, Lead.Status.INTERESTED,
            Lead.Status.FOLLOW_UP, Lead.Status.QUALIFIED,
            Lead.Status.CONVERTED,
        ]).count(),
        "qualified": in_range.filter(status__in=[
            Lead.Status.QUALIFIED, Lead.Status.CONVERTED,
        ]).count(),
        "converted": in_range.filter(status=Lead.Status.CONVERTED).count(),
        "lost": in_range.filter(status=Lead.Status.LOST).count(),
    }


def department_performance_report(start: datetime, end: datetime
                                  ) -> list[dict[str, Any]]:
    """
    Per-department roll-up:
      tasks_completed, activities, converted_leads, department_revenue.
    Revenue rule: payments recorded by users whose Employee is in the
    department.
    """
    from apps.departments.models import Department

    activity_agg = dict(SalesActivity.objects.filter(
        occurred_at__gte=start, occurred_at__lt=end,
        performed_by__department__isnull=False,
    ).values("performed_by__department_id").annotate(n=Count("id"))
    .values_list("performed_by__department_id", "n"))

    task_agg = dict(Task.objects.filter(
        status=Task.Status.COMPLETED,
        completed_at__isnull=False,
        completed_at__gte=start, completed_at__lt=end,
        assignee__department__isnull=False,
    ).values("assignee__department_id").annotate(n=Count("id"))
    .values_list("assignee__department_id", "n"))

    converted_agg = dict(Lead.objects.filter(
        converted_at__isnull=False,
        converted_at__gte=start, converted_at__lt=end,
        assigned_to__department__isnull=False,
    ).values("assigned_to__department_id").annotate(n=Count("id"))
    .values_list("assigned_to__department_id", "n"))

    out = []
    for d in Department.objects.all():
        out.append({
            "department_id": str(d.id),
            "department": d.name,
            "activities": activity_agg.get(d.id, 0),
            "tasks_completed": task_agg.get(d.id, 0),
            "conversions": converted_agg.get(d.id, 0),
        })
    return sorted(out, key=lambda r: -(r["activities"] + r["tasks_completed"]))


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
