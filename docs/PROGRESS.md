# Progress log

## Phase 0 — Discovery & Architecture — ✅ Complete
## Phase 1 — Technical Foundation — ✅ Complete
## Phase 2 — Authentication & Access Control — ✅ Complete
## Phase 3 — Leads & Customers — ✅ Complete
## Phase 4 — Sales, Tasks & Notifications — ✅ Complete
## Phase 5 — Management Dashboard — ✅ Complete
## Phase 6 — Webinars — ✅ Complete
## Phase 7 — Finance — ✅ Complete
## Phase 8 — Marketing & Reports — ✅ Complete

## Phase 9 — Integrations — 🚧 In progress

Delivered:

- **Permissions**: `integrations.read` + `integrations.manage` seeded
  for Owner / Admin (Finance gets read). Migration
  `accounts/0004_add_integrations_permissions`.

- **Adapter layer** under `apps/integrations/adapters/`:
  - `base.py` — `IntegrationStatus` dataclass + `env()` helper.
  - `razorpay.py` — full adapter:
    - `verify_signature` HMAC-SHA256 with constant-time comparison.
    - `handle_event` dispatches by `event`:
      * `payment.captured` → `record_payment(status=SUCCESSFUL,
        method=GATEWAY, source=GATEWAY, transaction_reference=pay_id,
        external_event_ref=event_id)` against the matching customer
        (email-normalised first, then phone).
      * `payment.failed` → records a FAILED payment row for audit
        continuity; duplicates are silently skipped.
      * `refund.processed` → `record_refund` against the previously
        recorded gateway payment by `payment_id`.
      * Unknown types → event stored, marked PROCESSED, no side effect.
  - `email_adapter.py` — Django `EmailMultiAlternatives` wrapper reading
    standard SMTP env vars; falls back to console backend when
    `EMAIL_HOST` is unset so nothing silently drops.
  - `whatsapp.py` — stub: same interface a real impl will expose
    (`send_text`), returns `{"sent": false, "reason": …}` with a log
    entry. Real send intentionally off until credentials + template
    approvals are in.

- **Webhook endpoint**:
  - `POST /api/v1/integrations/webhooks/razorpay/`
  - CSRF-exempt, `AllowAny`, custom `webhook` throttle scope
    (120/min).
  - **Signature verified before anything is stored** — a bad signature
    returns 400 without burning a dedup key.
  - Uses `ingest_webhook_event` from Phase 7, so replay is free: unique
    `(provider, provider_event_id)` guarantees at-most-once processing.
  - Handler failures mark the event FAILED with the exception text,
    leaving the dedup key held so Razorpay can retry safely.

- **Status endpoint**:
  - `GET /api/v1/integrations/status/`
  - Gated by `integrations.read`.
  - Returns `{name, label, enabled, configured, last_event_at,
    details}` per integration.

- **Email outbound wired**: `accounts/services.py.
  emit_password_reset_delivery` now calls `send_html_email` from the
  adapter. No SMTP → console backend prints the mail, no silent drop.

- **Settings**: `EMAIL_BACKEND` auto-selects SMTP vs console based on
  `EMAIL_HOST`; standard email env vars plumbed through. New throttle
  rate `webhook` = 120/min.

- **Frontend**: nav adds **Integrations** (role-gated); page at
  `/settings/integrations` shows each adapter's status + last event
  time + env hint. No CRUD — secrets live in the server environment.

- **`.env.example`** gains the integrations block.

Tests (`tests/test_integrations.py`, 7 cases):
- Bad signature → 400 and **no `WebhookEvent` row** (dedup key not
  burned).
- `payment.captured` → creates one Payment; replay is idempotent, still
  one.
- Unknown event type → stored, PROCESSED, no Payment row.
- `payment.captured` with no customer match → explicit `skipped`
  result, no Payment.
- Email adapter: `locmem` backend confirms the message hits `outbox`
  with the right recipient / subject / body.
- Status endpoint: 403 for Salesperson (no `integrations.read`); 200
  for Owner with correct `configured` reflection.

Exit criteria:

- [x] Real signature verification (HMAC-SHA256, constant-time).
- [x] Replay is idempotent via existing `WebhookEvent` unique constraint.
- [x] No silent success paths — failures audit + surface.
- [x] Configured-vs-enabled state is reflected in a single endpoint.
- [x] Secrets never leave the server environment.
