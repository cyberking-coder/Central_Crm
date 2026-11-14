# Progress log

## Phase 0 — Discovery & Architecture — ✅ Complete
## Phase 1 — Technical Foundation — ✅ Complete
## Phase 2 — Authentication & Access Control — ✅ Complete
## Phase 3 — Leads & Customers — ✅ Complete
## Phase 4 — Sales, Tasks & Notifications — ✅ Complete
## Phase 5 — Management Dashboard — ✅ Complete
## Phase 6 — Webinars — ✅ Complete

## Phase 7 — Finance — 🚧 In progress

Delivered (backend):

- **Models**: `Invoice`, `InvoiceItem`, `InvoiceSequence`, `Payment`,
  `Refund`, `Expense`, `WebhookEvent`. Every money column is
  `Decimal(14, 2)`; currency stored explicitly as ISO-3.
- **`on_delete` is PROTECT** everywhere ledger integrity matters:
  `Invoice.customer`, `Payment.customer`, `Payment.invoice`,
  `Refund.payment`. Customer/invoice can't be casually deleted.
- **Invoice numbering**: atomic `SELECT FOR UPDATE` on
  `InvoiceSequence(year)` → `INV-2026-00001`. No gaps under
  concurrency.
- **Services** (`apps/finance/services/`):
  - `invoices.create_invoice` — clients only submit items, server
    computes line amounts, subtotal, tax, discount, total. Rounding uses
    `ROUND_HALF_UP` at 2 decimal places.
  - `invoices.issue_invoice` / `void_invoice` — state machine
    enforcement (paid can't be voided, draft can't be voided-then-paid).
  - `invoices.recompute_invoice_status` — called after every payment or
    refund; promotes between ISSUED → PARTIALLY_PAID → PAID based on the
    ledger, never on a frontend hint.
  - `payments.record_payment` — rejects non-positive amounts, mismatched
    currencies, and duplicate `(method, transaction_reference)` via a
    partial unique constraint.
  - `payments.record_refund` — refuses over-refunds; flips payment status
    to REFUNDED vs PARTIALLY_REFUNDED based on the running total.
  - `webhooks.ingest_webhook_event` — idempotent store-then-process using
    the `(provider, provider_event_id)` unique constraint; failure marks
    the row FAILED without rolling back the dedup key.
- **Analytics (Part 17 #2 now ✅)**: `apps/analytics/services.py`
  gained `gross_collections_in_range`, `refunds_in_range`,
  `net_collections_in_range`, `outstanding_invoice_total`,
  `pending_payment_total`, `expenses_in_range`. `today_payload` and
  `weekly_payload` now include the finance block. The reconciliation
  test guarantees API ≡ service for finance numbers too.
- **API** under `/api/v1/finance/`:
  - `invoices/` CRUD + `issue`, `void`, `export` actions.
  - `payments/` CRUD + `refund`, `export` actions.
  - `expenses/` CRUD.
- **Admin**: `WebhookEvent` is read-only (no add / edit / delete) — same
  posture as `AuditLog`.

Delivered (frontend):

- Nav adds **Finance**.
- `/finance` hub with three cards.
- `/finance/invoices` list + CSV export.
- `/finance/invoices/new` — multi-line item form with live total preview.
- `/finance/invoices/[id]` — detail with line items, running totals, and
  an action bar: Issue / Record payment (inline form) / Void.
- `/finance/payments` list + CSV export.
- Dashboard: new "Today — Finance" row with 5 money KPIs for anyone
  carrying `finance.read` (role-gated at render time).

Tests (`tests/test_finance.py`, 14 cases):
- Server-side total computation (2×100 @ 18% + 50 → 286.00).
- Discount caps at zero.
- Invoice number is strictly sequential.
- Full payment → PAID; partial → PARTIALLY_PAID.
- Duplicate `(method, reference)` rejected.
- Currency mismatch rejected.
- Full refund → REFUNDED; partial → PARTIALLY_REFUNDED; over-refund
  rejected.
- Void on PAID rejected.
- Webhook idempotency: replay reuses existing row, handler called once.
- Failed handler → event marked FAILED with error, dedup key still held.
- Dashboard API ≡ analytics service for `gross_collections` and
  `net_collections`.
- Customer Support cannot create invoices.

Exit criteria:

- [x] Decimal money + explicit currency across every row
- [x] Atomic invoice numbering under concurrency
- [x] Server-only totals; clients can't forge amounts
- [x] Idempotent webhook ingestion (Part 17 #4)
- [x] Centralised financial calculations (Part 17 #2)
- [x] Dashboard numbers reconcile with reports
- [x] Refund + void guard rails
- [x] PROTECT on customer / invoice / payment FKs
