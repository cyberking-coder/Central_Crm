# Central Company CRM

Centralised CRM and company management platform. Single-company deployment.

## Stack

- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
- **Backend:** Django + Django REST Framework
- **Database:** PostgreSQL (Supabase-managed in production)
- **Infra:** Docker Compose for local dev

## Monorepo layout

```
apps/
  frontend/     # Next.js app
  backend/      # Django app (authoritative)
packages/
  api-types/    # Shared TS types generated from OpenAPI
infrastructure/
  docker/
docs/           # PRD, architecture, ERD, API, permissions, security, decisions
scripts/
```

## Local development

```bash
cp .env.example .env
docker compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API health: http://localhost:8000/api/v1/health/
- API docs: http://localhost:8000/api/v1/docs/

## Documentation

- `docs/PRD.md` — product requirements
- `docs/architecture.md` — technical architecture
- `docs/risk-controls.md` — Part 17 engineering risk controls (live status)
- `docs/PROGRESS.md` — per-phase progress log
- `docs/CHANGELOG.md`
- `docs/KNOWN_ISSUES.md`
- `docs/decisions/` — ADRs

## Phased delivery

See `docs/PROGRESS.md`. Each phase ends with a Phase Completion Report and requires explicit approval before the next phase begins.
