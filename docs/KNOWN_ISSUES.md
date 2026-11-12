# Known issues

## Phase 2

- **Password reset email delivery deferred.** The reset link is written to
  backend JSON logs instead of being emailed. A real email adapter lands
  in Phase 9 (Integrations). Operations can read `password_reset_link`
  entries from the logs and relay the link manually in the meantime.
- Phase-0 open questions still awaiting final answers (duplicate-matching
  rules, round-robin, currency policy, Supabase Storage, invoice
  numbering, deployment target). Current defaults from the Phase-0 plan
  remain in force.
- `tests/` are committed but not executed in the authoring sandbox; run
  `docker compose exec backend pytest` after `docker compose up`.
