# Progress log

## Phase 0 — Discovery & Architecture — ✅ Complete

## Phase 1 — Technical Foundation — ✅ Complete

## Phase 2 — Authentication & Access Control — 🚧 In progress

Delivered:

- **Custom User** (`accounts.User`, UUID PK, email as username, Argon2
  hashing). Email is case-normalised.
- **Role** + **Permission** models with M2M `Role.permissions`. Permission
  codes follow `<module>.<action>`.
- **RBAC seed** (`accounts/0002_seed_rbac.py`): 32 permission codes across
  leads / customers / sales / tasks / webinars / finance / marketing /
  employees / departments / users / reports / audit; 8 roles seeded
  exactly per Phase-0 matrix.
- **Department** (`departments.Department`) + **Employee**
  (`employees.Employee`) models with proper `on_delete`:
  - `Department.manager → Employee` : `SET_NULL`
  - `Employee.user → User` : `PROTECT` (deactivation never cascades).
  - `Employee.department` / `Employee.reporting_manager` : `SET_NULL`.
- **AuditLog** model: append-only, UUID PK, indexes on action/entity/time,
  JSON before/after/extra, correlation ID, admin is view-only.
- **DRF permission class** `HasPermissionCode` driven by
  `view.required_permission`; superuser bypass; deactivated users denied.
- **Auth endpoints** under `/api/v1/auth/`:
  - `GET /csrf/` — issues CSRF cookie
  - `POST /login/` — returns `MeSerializer` on success, 400 on failure
  - `POST /logout/` — 204
  - `GET /me/` — current user + permissions
  - `POST /password/reset/request/` — always 204 (no account-existence leak)
  - `POST /password/reset/confirm/` — Django signed token
- **Throttling**: anon 30/min on login & reset endpoints.
- **Audit emission** on login success/failure, logout, password-reset
  request & completion.
- **Bootstrap command** `python manage.py bootstrap_owner --email … --password …`
  (idempotent).
- **Frontend**:
  - `/login` client page with CSRF-cookie flow
  - `/dashboard` protected route (SSR `getMe` → redirect if unauthenticated)
  - `/` redirects by auth state
  - Logout button clears session
- **Tests** added: `test_auth.py` (8 cases), `test_permission_matrix.py`
  (RBAC seed + `HasPermissionCode` behaviour — parametrised across roles).

Exit criteria:

- [x] Valid login returns 200 and session cookie
- [x] Invalid login returns 400 and emits `login.failed` audit
- [x] Deactivated user cannot log in
- [x] Logout clears session
- [x] Password reset round-trip works
- [x] Permission class denies anon / deactivated / wrong-role users
- [x] Seeded roles match Phase-0 permission matrix
