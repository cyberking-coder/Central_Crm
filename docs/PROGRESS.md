# Progress log

## Phase 0 — Discovery & Architecture — ✅ Complete
## Phase 1 — Technical Foundation — ✅ Complete
## Phase 2 — Authentication & Access Control — ✅ Complete
## Phase 3 — Leads & Customers — ✅ Complete
## Phase 4 — Sales, Tasks & Notifications — ✅ Complete
## Phase 5 — Management Dashboard — ✅ Complete
## Phase 6 — Webinars — ✅ Complete
## Phase 7 — Finance — ✅ Complete

## Phase 8 — Marketing & Reports — 🚧 In progress

Delivered (backend):

- **Campaign gets `currency` + `spend`** fields; migration
  `marketing/0003`.
- **`apps/analytics/services.py` grows four reports**, each reading the
  same tables the dashboard and CSV exports do (Part 17 #2 reuse):
  - `source_performance_report` — per source: leads, qualified,
    converted, conversion %, attributed revenue (first-touch rule
    documented in the docstring).
  - `campaign_performance_report` — per campaign: leads, converted,
    spend, attributed revenue, cost-per-lead, ROI %.
  - `conversion_funnel` — leads / contacted / qualified / converted /
    lost for the range.
  - `department_performance_report` — per department: activities, tasks
    completed, conversions.
- **Report endpoints** under `/api/v1/analytics/reports/`:
  - `sources/`, `campaigns/`, `funnel/`, `departments/`.
  - `<kind>/export/` → CSV via `write_csv` (Part 17 #10) with the
    report-exported audit emitted.
  - All gated by `reports.read`; `from` + `to` date params, falls back
    to the current week.
- **Public lead capture**: `POST /api/v1/leads/public/` is
  unauthenticated (dedicated throttle rate `public_leads` = 10/min),
  parses UTM parameters, finds campaign by `utm_campaign` (case
  insensitive) or name, applies the usual duplicate detection AND
  returns `200 OK` on duplicates so forms can't fingerprint existence.
  Successful inserts emit `lead.public_created` audit; silent dedup
  emits `lead.public_duplicate`.

Delivered (frontend):

- Nav adds **Campaigns** and **Reports**.
- `/marketing/campaigns` list + `/marketing/campaigns/new` (name,
  source, UTM triple, spend, currency, active).
- `/reports` hub with 4 cards.
- `/reports/sources` — table with conversion % + revenue + CSV export.
- `/reports/campaigns` — CPL and ROI columns; ROI colour-coded.
- `/reports/funnel` — horizontal bar chart (5 stages) built with plain
  Tailwind; "Lost in range" counted separately.
- `/reports/departments` — table + CSV export.
- Shared **date range picker** (`components/date-range.tsx`) used by
  every report; sensible default (this week).

Tests (`tests/test_reports.py`, 10 cases):
- Source report counts across 2 sources + attributed revenue by
  converted-customer.source.
- Campaign report computes CPL=333.33 and ROI=200% for spend=1000
  revenue=3000 leads=3.
- Funnel counts respect status classifications (QUALIFIED + CONVERTED
  both counted as qualified).
- API endpoint reconciles against the service function row-by-row.
- CSV export sanitiser invoked (content-type assertion).
- `reports.read` enforcement (Customer Support → 403).
- Public capture: creates and attributes to the right campaign.
- Public capture: dedupe returns 200 without creating a second row.
- Public capture requires no auth.

Exit criteria:

- [x] Reports fed from the same service module as the dashboard
- [x] CPL, ROI, conversion rate computed server-side
- [x] Date-range filters on every report
- [x] CSV export for every table
- [x] Public UTM capture + first-touch attribution working
- [x] Rate limiting on public endpoint
