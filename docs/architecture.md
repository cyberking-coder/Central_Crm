# Architecture

## Topology

```
┌──────────────┐    HTTPS + cookie session    ┌─────────────────┐    psycopg3    ┌──────────────┐
│ Next.js 14   │ ─────────────────────────▶  │ Django 5 + DRF  │ ─────────────▶ │ PostgreSQL   │
│ (App Router) │                              │ /api/v1/*       │                │ (Supabase)   │
└──────────────┘                              └─────────────────┘                └──────────────┘
```

- Next.js is a pure UI layer. It never computes authoritative numbers.
- Django owns business rules, permissions, migrations, aggregations.
- Supabase is **managed Postgres only** — no Supabase Auth, no SQL Editor changes.

## Modules (Django apps)

Each domain lives in its own app under `apps/backend/apps/`:
`core`, `accounts`, `employees`, `departments`, `leads`, `customers`, `sales`,
`tasks`, `webinars`, `finance`, `marketing`, `notifications`, `analytics`,
`audit`, `integrations`, `api`.

## Cross-cutting concerns (owned by `apps/core`)

- UUID + timestamp model mixins.
- Timezone helpers (UTC storage, company TZ display, DST-safe half-open ranges).
- CSV export sanitiser (formula-injection safe).
- Correlation-ID middleware (JSON logs).

## API surface

- Versioned prefix: `/api/v1/`.
- Session cookie auth; CSRF token on mutations.
- DRF exception handler returns a consistent `{ "error": {...}, "request_id": ... }` envelope.
- OpenAPI served at `/api/v1/schema/`, Swagger UI at `/api/v1/docs/`.

## Business-logic placement

- **Serializers** validate shape.
- **Services** (plain Python callables / classes in `apps/<x>/services/`) own domain logic.
- **Viewsets** are thin: permission check → service call → serializer.
- Multi-record workflows run in `transaction.atomic()`.

## Risk controls

See `docs/risk-controls.md` for the live status of every Part 17 control.
