# n8n (and other automation tools) integration

Central CRM exposes a REST API under `/api/v1/` that n8n, Zapier, Make,
Pipedream, Airtable scripts, custom cron jobs — anything that can make
an HTTPS request — can pull from and push to.

## 1. Create an API token

1. In the CRM, open **API tokens** in the top nav.
2. Enter a name (e.g. `n8n-production`) → **Create token**.
3. Copy the token that appears. It is shown exactly once.

Treat the token like a password. It carries your full permissions.

Revoke a token any time from the same page.

## 2. Authenticate

Every request to `/api/v1/` (except `/auth/login/`, `/auth/csrf/` and
`/leads/public/`) needs this header:

```
Authorization: Bearer ccrm_xxxxxxxxxxxxxxxxxxxxxx
```

No cookies, no CSRF token, no CORS worries. Works from server-to-server
or any HTTP client.

## 3. Common n8n recipes

### Push a new lead from a Typeform / Google Form webhook

n8n **HTTP Request** node:

- **Method:** POST
- **URL:** `https://centralcrm-frontend.vercel.app/api/v1/leads/`
- **Headers:**
  - `Authorization`: `Bearer YOUR_TOKEN`
  - `Content-Type`: `application/json`
- **Body (JSON):**
  ```json
  {
    "full_name": "{{ $json.name }}",
    "email": "{{ $json.email }}",
    "phone": "{{ $json.phone }}",
    "source": "<lead-source-uuid>",
    "interested_product": "{{ $json.product }}"
  }
  ```

Response is the created lead JSON including its `id`. If the lead is a
duplicate the API returns 400 and a message in the response body.

### Push a lead with no login at all (public form)

For embedding in forms that can't hold a secret:

- **URL:** `https://centralcrm-frontend.vercel.app/api/v1/leads/public/`
- No `Authorization` header.
- Rate limit: 10 requests per minute per IP.
- Duplicates return 200 with `{"ok": true}` so the form can't fingerprint
  who's already in the system.

### Pull today's leads (for a Slack digest in n8n)

- **Method:** GET
- **URL:** `https://centralcrm-frontend.vercel.app/api/v1/leads/?status=new&ordering=-created_at`
- **Headers:** `Authorization: Bearer YOUR_TOKEN`

Response is paginated:
```json
{
  "count": 42,
  "next": "...",
  "previous": null,
  "results": [ { "id": "...", "full_name": "...", ... } ]
}
```

### Record a Razorpay payment automatically

Webhook is already wired. In the Razorpay dashboard:

- **URL:** `https://centralcrm-frontend.vercel.app/api/v1/integrations/webhooks/razorpay/`
- **Events:** `payment.captured`, `payment.failed`, `refund.processed`
- Copy the webhook secret into Render env var `RAZORPAY_WEBHOOK_SECRET`.

The CRM creates matching `Payment` rows automatically (no API token
needed — signature verification protects the endpoint). Duplicate
deliveries are deduplicated by event id.

### Create a task from an external event

- `POST /api/v1/tasks/` with:
  ```json
  {
    "title": "Call back John",
    "description": "Interested in enterprise plan",
    "assignee": "<employee-uuid>",
    "due_at": "2026-12-15T10:00:00Z",
    "priority": "high",
    "related_kind": "lead",
    "related_id": "<lead-uuid>"
  }
  ```

The assignee gets an in-app notification automatically.

### Create an invoice

- `POST /api/v1/finance/invoices/` with:
  ```json
  {
    "customer": "<customer-uuid>",
    "items": [
      { "description": "Consulting, Nov",
        "quantity": "10", "unit_price": "5000.00", "tax_rate": "18.000" }
    ],
    "notes": "Invoice from monthly billing job"
  }
  ```

Totals are computed server-side. The invoice is created in `draft`
status; `POST /api/v1/finance/invoices/{id}/issue/` to mark it issued.

## 4. API reference

- **Swagger UI:** https://centralcrm-frontend.vercel.app/api/v1/docs/
- **OpenAPI schema:** https://centralcrm-frontend.vercel.app/api/v1/schema/

Point n8n's **HTTP Request → Import from cURL** at the schema for
auto-complete of every endpoint.

## 5. What tokens can and can't do

- A token carries the permissions of the user who created it. If you want
  a token with restricted permissions (e.g. only `leads.create`), create
  a separate user with that role and generate the token as that user.
- Tokens never expire on their own. Revoke them manually from the
  **API tokens** page.
- Token keys are stored as SHA-256 hashes in the database — if the DB
  ever leaks, your tokens are not readable.
- Every token use updates `last_used_at` (throttled to once per minute)
  so you can see at a glance whether an integration is still active.
