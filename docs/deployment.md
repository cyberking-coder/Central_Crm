# Deployment

**Stack in production**

- Database: Supabase (Postgres, managed).
- Backend: Render (gunicorn), region `singapore` (close to Supabase ap-south-1).
- Frontend: Vercel.
- Scheduled sweeps: Render Cron (every 5 minutes).

**Repo layout the platforms expect**

- `apps/backend/` — Django project, deployed by Render.
- `apps/frontend/` — Next.js app, deployed by Vercel.
- `render.yaml` — Blueprint for Render (web + 2 crons).
- `apps/frontend/vercel.json` — tells Vercel it's a subfolder Next.js app.

---

## 1. Backend on Render

1. Sign in at https://render.com with your GitHub account.
2. **New → Blueprint**, pick `cyberking-coder/Central_Crm` branch
   `claude/loving-mccarthy-iuv18j` (or `main` after you merge). Render
   reads `render.yaml` and proposes three services.
3. Click **Apply**. When Render asks for the `sync: false` variables,
   fill them in from your Supabase project:
   - `POSTGRES_HOST` = `db.<ref>.supabase.co`
   - `POSTGRES_PASSWORD` = your Supabase DB password
   - `DJANGO_ALLOWED_HOSTS` = `<your-backend>.onrender.com`
   - Leave `DJANGO_CSRF_TRUSTED_ORIGINS` and
     `DJANGO_CORS_ALLOWED_ORIGINS` blank for now — you fill them in
     after the frontend goes live.
4. First deploy takes ~5 minutes. When it says `Live`:
   ```
   curl https://<your-backend>.onrender.com/api/v1/health/
   ```
   Should return the same payload you see locally.

### Create the first user

Render → service → **Shell** tab:

```
python manage.py bootstrap_owner --email you@example.com --password 'something-strong' --full-name 'Owner'
```

### Optional: integrations

Add these env vars in the Render service's **Environment** tab as you
turn each integration on:

- `RAZORPAY_WEBHOOK_SECRET`
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
  `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`
- `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`

---

## 2. Frontend on Vercel

1. Sign in at https://vercel.com with your GitHub account.
2. **Add New → Project**, pick the same repo. In the **Configure
   Project** screen:
   - **Root Directory** → click Edit → set to `apps/frontend`.
   - Framework detection: Next.js (automatic).
3. Add environment variables:
   - `NEXT_PUBLIC_API_BASE_URL` = `https://<your-backend>.onrender.com/api/v1`
   - `INTERNAL_API_BASE_URL` = `https://<your-backend>.onrender.com/api/v1`
4. Deploy. First build takes a couple of minutes.
5. Copy the production URL (e.g. `https://central-crm.vercel.app`).

### Wire the frontend origin back into the backend

Go back to Render → backend service → **Environment**:

- `DJANGO_CSRF_TRUSTED_ORIGINS` = `https://central-crm.vercel.app`
- `DJANGO_CORS_ALLOWED_ORIGINS` = `https://central-crm.vercel.app`

Save → Render redeploys automatically. Open the Vercel URL and sign in.

---

## 3. Verify

1. Open the Vercel URL → log in with the owner account.
2. Create a lead, convert it, record a payment on the invoice detail.
3. Open the Render service **Logs** tab — you'll see per-request JSON lines.
4. Open the Supabase Table editor → `leads_lead`, `finance_invoice`,
   `finance_payment` all show your rows.

## 4. Custom domain

- **Frontend domain** (e.g. `app.example.com`): Vercel → Project →
  Settings → Domains → Add. Vercel provides a CNAME.
- **Backend domain** (e.g. `api.example.com`): Render → service →
  Settings → Custom Domains → Add.
- Update Render env vars:
  - `DJANGO_ALLOWED_HOSTS` = `api.example.com`
  - `DJANGO_CSRF_TRUSTED_ORIGINS` = `https://app.example.com`
  - `DJANGO_CORS_ALLOWED_ORIGINS` = `https://app.example.com`
- Update Vercel env var:
  - `NEXT_PUBLIC_API_BASE_URL` = `https://api.example.com/api/v1`
- Redeploy both.

## 5. Ongoing

- Every push to the deployed branch auto-deploys (Render + Vercel both watch GitHub).
- Migrations run automatically via `build.sh`.
- The two Render crons run the overdue sweeps.
- Backups: Supabase's automatic daily backups cover the database.

## Troubleshooting

- **502 on backend**: Render → Logs. Most likely a missing env var or a migration failure. The health check endpoint (`/api/v1/health/`) tells you whether the DB is reachable.
- **CORS error in the browser**: `DJANGO_CORS_ALLOWED_ORIGINS` doesn't include the exact origin. Must match scheme + host + port (no trailing slash).
- **Session cookie not persisting**: happens when the two apps are on different sites. Production settings already set `SameSite=None; Secure` when `DEBUG=0`, which is correct for Vercel+Render on different domains. If you move both to subdomains of one domain, switch to `SameSite=Lax` for better protection.
