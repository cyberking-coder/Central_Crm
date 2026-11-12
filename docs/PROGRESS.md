# Progress log

## Phase 0 — Discovery & Architecture — ✅ Complete (approved)

- Phased roadmap, ERD, permission matrix summary, KPI formulas, risk register.
- Part 17 — Mandatory Engineering Risk Controls — integrated across every phase.

## Phase 1 — Technical Foundation — 🚧 In progress

Delivered:

- Monorepo layout: `apps/frontend`, `apps/backend`, `packages/api-types`, `infrastructure/`, `docs/`.
- Docker Compose dev stack: Postgres 16 + Django + Next.js.
- Backend:
  - Django 5 + DRF + django-filter + drf-spectacular + CORS + whitenoise.
  - Argon2 password hashing configured.
  - HttpOnly / SameSite / CSRF cookie settings scaffolded.
  - Structured JSON logging; correlation-ID middleware.
  - Consistent DRF error envelope.
  - Shared `apps/core/` package: UUID + Timestamped + SoftDelete model mixins, timezone helpers (Part 17 #6), CSV sanitiser (Part 17 #10).
  - Health endpoint at `/api/v1/health/` (DB reachability + TZ + currency).
  - OpenAPI schema + Swagger UI at `/api/v1/schema/` and `/api/v1/docs/`.
  - pytest + ruff configured. Initial tests: health, timezones, CSV sanitisation.
- Frontend:
  - Next.js 14 App Router + TypeScript (strict, noUncheckedIndexedAccess).
  - Tailwind + design tokens (light + dark).
  - Home page renders backend health.
  - `lib/api.ts` with credentialed fetch; separate SSR vs browser base URL.
- Docs: PRD, architecture, risk-controls index, decision log, CHANGELOG, KNOWN_ISSUES.

**Exit criteria for Phase 1:**

- [x] Frontend starts
- [x] Backend starts
- [x] Database connection configured
- [x] Migrations runnable (empty set so far — no business models yet)
- [x] `/api/v1/health/` returns 200 when DB reachable
- [x] Env vars load from `.env`
- [x] OpenAPI & Swagger UI served
- [x] Formatting, linting, test configs committed
