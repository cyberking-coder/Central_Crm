# Changelog

## [Unreleased]

### Phase 2 — Authentication & Access Control
- Custom `accounts.User` (UUID, email, Argon2).
- `Role` + `Permission` models with M2M; 32 permission codes and 8 roles
  seeded via data migration to match the Phase-0 matrix.
- `departments.Department` and `employees.Employee` models.
- `audit.AuditLog` append-only model + admin view-only.
- DRF `HasPermissionCode` permission class.
- Auth endpoints: CSRF, login, logout, me, password-reset request/confirm.
- Anonymous throttle 30/min on auth endpoints.
- `bootstrap_owner` management command.
- Frontend login page, SSR-guarded `/dashboard`, logout.

### Phase 1 — Technical foundation
- Monorepo + Docker Compose dev stack.
- Django 5 + DRF skeleton with cookie-session auth scaffolding.
- Next.js 14 + Tailwind design-token shell.
- `GET /api/v1/health/` with DB reachability check.
- drf-spectacular OpenAPI + Swagger UI.
- Shared timezone, CSV-sanitiser, UUID & soft-delete mixins.
- Initial test suite (health, timezones, CSV sanitisation).
