# Part 17 — Mandatory Engineering Risk Controls

| # | Control | Status | Evidence |
|---|---|---|---|
| 1 | Django-only schema ownership | ✅ | All migrations committed; ADR 0001 |
| 2 | **Centralised financial calculations** | ✅ landed | `apps/analytics/services.py` is the single source for KPI AND finance formulas; dashboard endpoints and reports both import from it; `test_finance.test_dashboard_finance_fields_reconcile` enforces API ≡ service |
| 3 | Permission enforcement matrix | ✅ | `HasPermissionCode` per viewset; finance.read/manage/export gated; `test_finance.test_support_cannot_create_invoice` |
| 4 | **Webhook idempotency** | ✅ landed | `WebhookEvent` with `(provider, provider_event_id)` unique; `ingest_webhook_event` service; `test_finance.test_duplicate_webhook_not_reprocessed` + failure-marks-FAILED test |
| 5 | Data retention & deletion | ✅ | PROTECT on `Invoice.customer`, `Payment.customer`, `Payment.invoice`, `Refund.payment`. `AuditLog` and `WebhookEvent` admin read-only. |
| 6 | Timezone correctness | ✅ | `apps/core/timezones.py` used by all range queries |
| 7 | Duplicate detection | ✅ | Leads (phone/email normalised), webinar registrations (DB partial unique constraints), payments (method + reference unique) |
| 8 | Background job reliability | ✅ | Celery with retries + time limits; DB-dedup idempotent sweeps |
| 9 | Dashboard performance | ✅ | `assertNumQueries ≤ 25` on today endpoint |
| 10 | Export & data security | ✅ | `write_csv` sanitiser; `*.export` permissions on leads/customers/invoices/payments |
| 11 | Verification | ✅ | Phase Completion Report §12 |
