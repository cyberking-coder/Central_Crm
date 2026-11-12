# ADR 0001 — Django owns the database schema

**Status:** Accepted (Phase 1)

## Context
We use Supabase as managed PostgreSQL. Supabase offers a SQL Editor that
tempts ad-hoc schema changes. Mixed ownership causes drift between
`django_migrations` state and the live DB.

## Decision
- Django migrations are the **sole** source of schema truth.
- The Supabase SQL Editor is **not** used against the production database for
  schema changes. (Row-level reads for debugging are allowed.)
- Every schema change ships as a committed migration file, reviewed in PR.
- CI runs `python manage.py makemigrations --check --dry-run` to detect drift.
- Already-applied migrations are not edited in place; corrections ship as new
  migrations.

## Consequences
- Rollback planning is a Django concern (data migrations reversible where
  practical; irreversible ones documented).
- Supabase-specific features (extensions, RLS policies if ever used) are
  declared through `RunSQL` operations inside Django migrations so they are
  version-controlled.
