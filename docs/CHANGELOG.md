# Changelog

## [Unreleased]

### Phase 8 — Marketing & Reports
- Campaign gains currency + spend fields (marketing/0003).
- analytics/services adds 4 report functions sharing the dashboard's data path:
  sources (leads, qualified, conv %, revenue), campaigns (CPL, ROI),
  funnel, departments.
- Endpoints /api/v1/analytics/reports/{sources, campaigns, funnel,
  departments} + /{kind}/export/, all gated by reports.read, with date range.
- Public lead capture at /api/v1/leads/public/ (10/min throttle, no auth,
  UTM-driven campaign attribution, silent dedup).
- Frontend: /reports hub + 4 report pages with shared date range picker +
  CSV export; /marketing/campaigns list + new form.

### Phase 7 — Finance
- apps/finance: Invoice, InvoiceItem, InvoiceSequence, Payment, Refund,
  Expense, WebhookEvent (Part 17 #4).
- Decimal(14,2) money, explicit ISO-3 currency, PROTECT on ledger FKs.
- Atomic invoice numbering via SELECT FOR UPDATE on per-year sequence.
- Services enforce server-side totals, state machine, refund guards.
- Analytics now serves finance KPIs (Part 17 #2 complete); dashboard
  gets a 5-card finance row for finance.read users.
- Endpoints: /api/v1/finance/{invoices,payments,expenses} with CRUD plus
  issue/void and refund custom actions; CSV export on invoices+payments.
- 14 finance tests including API↔service reconciliation and webhook
  idempotency.

### Phase 6 — Webinars
- apps/webinars: Webinar, WebinarRegistration, WebinarAttendance models.
- Partial unique constraints on (webinar, email_normalised) and
  (webinar, phone_normalised) prevent duplicates at the DB level too.
- Services: register_for_webinar (capacity + duplicate), cancel,
  record_attendance (derives duration), webinar_summary.
- Endpoints: CRUD, /{id}/register, /{id}/registrations, /{id}/stats,
  /registrations, /attendance (PATCH).
- Frontend: /webinars list + new + detail with stats + registration panel.
- Nav adds Webinars.

### Phase 5 — Management Dashboard
- apps/analytics/services.py: single-source KPI formulas (leads/activities/
  followups/tasks/customers, by day and week) with uniform
  employee/department/source filters; DST-safe via company TZ helpers.
- Endpoints: GET /api/v1/analytics/{dashboard/today, dashboard/weekly,
  leaderboard} — gated by reports.read.
- Reconciliation test: API payload matches service payload field-by-field.
- Performance tests: assertNumQueries ≤ 25 on today endpoint (Part 17 #9).
- Frontend: real Dashboard page (10 Today KPIs, 5 Weekly, leads-by-source,
  salesperson leaderboard) with drill-down links.

### Phase 4 — Sales, Tasks & Notifications
- sales.SalesActivity, sales.FollowUp, tasks.Task, notifications.Notification.
- Permissions seed +3 codes (sales.followup.read/manage, notifications.read).
- Services: activity logging updates last_contacted + customer timeline;
  follow-up complete/cancel; task complete; idempotent overdue sweeps.
- Lead assignment now sends a notification to the assignee.
- APIs: /sales/activities, /sales/followups (+ complete/cancel),
  /tasks (+ complete/mine), /notifications (+ mark_read/all/unread_count).
- Celery broker (Redis) + worker + beat added to docker-compose;
  sweep tasks every 5 minutes (Part 17 #8). Management commands available
  for cron-based deploys.
- Frontend: notification bell, /tasks page with My/Overdue/All tabs,
  activity + follow-up panel on lead detail.

### Phase 3 — Leads & Customers
(See previous entry.)

### Phase 2 — Authentication & Access Control
(See previous entry.)

### Phase 1 — Technical foundation
(See previous entry.)
