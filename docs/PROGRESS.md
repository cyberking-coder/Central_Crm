# Progress log

## Phase 0 — Discovery & Architecture — ✅ Complete
## Phase 1 — Technical Foundation — ✅ Complete
## Phase 2 — Authentication & Access Control — ✅ Complete
## Phase 3 — Leads & Customers — ✅ Complete
## Phase 4 — Sales, Tasks & Notifications — ✅ Complete

## Phase 5 — Management Dashboard — 🚧 In progress

Delivered:

- **`apps/analytics/services.py`** — single source for every KPI formula,
  documented and reused by the dashboard endpoints (and later by reports
  and the AI assistant). Metrics implemented:
  - `leads_created_in_range`, `leads_assigned_in_range` (events, not state),
    `leads_unassigned_now`.
  - `customers_converted_in_range`.
  - `activities_in_range` (optional `kind`), `followups_due_in_range`,
    `followups_overdue_now`.
  - `tasks_overdue_now`, `tasks_completed_in_range`.
  - `leads_by_source_in_range`.
  - `salesperson_leaderboard` (activities + conversions).
  - Composite `today_payload`, `weekly_payload`.
- **Filters** (`Filters` dataclass): employee / department / source;
  applied uniformly across leads, customers, activities, follow-ups,
  tasks.
- **Timezone handling**: all day/week boundaries pass through
  `apps.core.timezones.company_day_range_utc` /
  `company_week_range_utc` (Part 17 #6), so filters are DST-safe.
- **Endpoints** under `/api/v1/analytics/`:
  - `GET dashboard/today/` (accepts `date`, `employee`, `department`,
    `source`).
  - `GET dashboard/weekly/`.
  - `GET leaderboard/` (accepts `date`, `limit`).
  - All require `reports.read`.
- **Frontend**: real `/dashboard` page replaces the Phase-2 stub.
  10 Today KPI cards, 5 Weekly cards, leads-by-source breakdown, top-10
  salesperson leaderboard. KPI cards with hrefs drill into the leads /
  customers / tasks lists with the corresponding filter.

Tests (`tests/test_analytics.py`, 8 cases):
- Service formula checks for today payload (leads received, assigned,
  awaiting, calls, activities, followups_overdue, tasks_overdue).
- Filter narrowing (employee filter zeroes assignment count).
- Weekly payload shape incl. source breakdown.
- **Reconciliation**: API payload equals service payload field-by-field
  (so the dashboard cannot diverge from the single source).
- **Performance budget** (Part 17 #9): `assertNumQueries ≤ 25` on today,
  `≤ 20` on weekly.
- Permission: `Customer Support` (no `reports.read`) gets 403.
- Leaderboard returns at least the seeded employee with the right counts.

Exit criteria:

- [x] KPIs computed server-side only
- [x] Formulas live in one module reused by endpoints and tests
- [x] Dashboard payload reconciles with underlying records
- [x] Query budget enforced in tests (Part 17 #9)
- [x] All KPI endpoints permission-gated
- [x] Frontend renders live numbers and drills into lists
