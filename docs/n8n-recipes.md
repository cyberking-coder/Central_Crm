# n8n recipes — auto-sync everything

Every integration below is **built once in n8n**, then runs on schedule
or webhook. No code changes in the CRM.

Set these n8n credentials once:
- **Central CRM**: HTTP Header Auth → Name `Authorization`, Value
  `Bearer <API token from /settings/api-tokens>`.
- **Meta / Google / Zoom / Typeform** etc.: use n8n's built-in OAuth.

---

## 1. Meta Lead Ads → CRM (real-time)

A new lead from Meta appears in `/leads` within seconds.

Nodes:
1. **Facebook Lead Ads** trigger → pick your form.
2. **HTTP Request** →
   - Method: POST
   - URL: `https://centralcrm-frontend.vercel.app/api/v1/leads/`
   - Auth: Central CRM credential (Bearer token)
   - Body (JSON):
     ```json
     {
       "full_name": "{{$json.field_data.full_name}}",
       "phone":     "{{$json.field_data.phone_number}}",
       "email":     "{{$json.field_data.email}}",
       "source":    "<meta-facebook-lead-source-uuid>",
       "interested_product": "{{$json.ad_name}}"
     }
     ```
3. Save, activate.

---

## 2. Google Ads leads → CRM (real-time)

Same shape as Meta but with the **Google Ads Lead Form Extension** trigger.

---

## 3. Website form (Typeform / JotForm / WPForms / Google Forms) → CRM

For each form platform n8n has a native trigger node. Map the fields
to the same POST body as above.

If you'd rather skip authentication (embeddable public forms), use:
```
POST https://centralcrm-frontend.vercel.app/api/v1/leads/public/
```
No `Authorization` header needed, rate-limited to 10/min per IP, dedupes
silently.

---

## 4. Meta Ads spend & stats → CRM Ads dashboard (polled every hour)

Pushes campaign spend, impressions, clicks, conversions so the **Ads**
page in the CRM stays live.

Nodes:
1. **Schedule Trigger** → every hour.
2. **Facebook Graph API** (Read) →
   - Resource: `Insights`
   - URL: `act_<AD_ACCOUNT_ID>/insights`
   - Fields: `campaign_name,spend,impressions,clicks,actions,date_start`
   - Time range: `last_7d` or `yesterday`
   - Level: `campaign`
3. **Code** node (transform to the shape the CRM expects):
   ```javascript
   return items.map(i => ({ json: {
     utm_campaign: i.json.campaign_name,     // or pass campaign_id
     date:         i.json.date_start,
     spend:        i.json.spend,
     impressions:  Number(i.json.impressions || 0),
     clicks:       Number(i.json.clicks || 0),
     conversions:  Number((i.json.actions || [])
                     .filter(a => a.action_type === 'lead')
                     .reduce((s, a) => s + Number(a.value), 0)),
     currency:     'INR',
     source:       'meta_ads',
   }}));
   ```
4. **HTTP Request** →
   - Method: POST
   - URL: `https://centralcrm-frontend.vercel.app/api/v1/marketing/ad-metrics/`
   - Auth: Central CRM (Bearer)
   - Body: `{ "rows": {{$items().map(i => i.json)}} }`

> Each row is upserted by `(campaign, date)`, so re-running is safe
> and idempotent.

---

## 5. Google Ads spend & stats → CRM Ads dashboard

Same flow as Meta but with the **Google Ads** → **Report** node. Map
fields:
- `campaign.name` → `utm_campaign`
- `segments.date` → `date`
- `metrics.cost_micros / 1_000_000` → `spend`
- `metrics.impressions` → `impressions`
- `metrics.clicks` → `clicks`
- `metrics.conversions` → `conversions`
- `source: "google_ads"`

---

## 6. Zoom webinar attendance → CRM

Nodes:
1. **Zoom** trigger → `Webinar Participant Joined` / `Participant Left`.
2. **HTTP Request** (Lookup):
   `GET /api/v1/webinars/registrations/?webinar=<webinar-id>&...`
3. **HTTP Request** (Update):
   `PATCH /api/v1/webinars/attendance/<id>/` with
   `{"status": "attended", "joined_at": "...", "left_at": "..."}`.

Or simpler: collect attendance from Zoom's post-webinar report once,
then bulk update.

---

## 7. WhatsApp conversations → CRM (both directions)

Every WhatsApp message to/from a customer shows up on their
`/customers/<id>` page threaded. Uses WhatsApp Business Cloud API via
n8n.

**Inbound — customer messages us:**

1. In Meta: WhatsApp Business → Webhooks → point at your n8n webhook URL.
2. n8n **Webhook** trigger → **Code** node to extract:
   - `from` (the customer's number, e164)
   - `text.body`
   - `id` (message id)
   - `timestamp`
3. **HTTP Request** → POST `/api/v1/communications/ingest/` with:
   ```json
   {
     "channel": "whatsapp",
     "direction": "in",
     "contact_phone": "{{$json.from}}",
     "from_address":  "{{$json.from}}",
     "to_address":    "{{$env.OUR_BUSINESS_NUMBER}}",
     "body":          "{{$json.text.body}}",
     "external_ref":  "{{$json.id}}",
     "occurred_at":   "{{new Date($json.timestamp * 1000).toISOString()}}"
   }
   ```

**Outbound — salesperson sends from WhatsApp:**

Use the WhatsApp Business → Messages endpoint. After sending, POST the
same shape to the CRM with `direction: "out"`.

Dedup is automatic via `(channel, external_ref)` — replays of the Meta
webhook don't double-insert.

## 8. Email conversations → CRM

**Inbound (customer → us):**

1. n8n **Gmail** or **IMAP Email** trigger → "new email".
2. **HTTP Request** → POST `/api/v1/communications/ingest/` with:
   ```json
   {
     "channel": "email",
     "direction": "in",
     "contact_email": "{{$json.from.value[0].address}}",
     "from_address":  "{{$json.from.value[0].address}}",
     "to_address":    "{{$json.to.value[0].address}}",
     "subject":       "{{$json.subject}}",
     "body":          "{{$json.text}}",
     "external_ref":  "{{$json.messageId}}",
     "occurred_at":   "{{$json.date}}"
   }
   ```

**Outbound (us → customer):**

After your Gmail → send email action, chain another ingest POST with
`direction: "out"`.

## 9. Phone calls → CRM (Exotel / Twilio / Knowlarity)

Each provider sends a call-ended webhook with the recording URL and
duration:

1. n8n **Webhook** trigger → provider's post-call hook.
2. **HTTP Request** → POST `/api/v1/communications/ingest/` with:
   ```json
   {
     "channel": "call",
     "direction": "in",
     "contact_phone": "{{$json.from}}",
     "from_address":  "{{$json.from}}",
     "to_address":    "{{$json.to}}",
     "body":          "{{$json.transcription || ''}}",
     "duration_seconds": "{{$json.duration}}",
     "recording_url":   "{{$json.recording_url}}",
     "external_ref":    "{{$json.sid}}",
     "occurred_at":     "{{$json.end_time}}"
   }
   ```

Call recordings play inline on the CRM thread; transcripts (if your
provider returns them) show as the body.

## 10. Razorpay payments → CRM Finance (already wired)

Not n8n — Razorpay's dashboard webhook points directly at:
```
https://centralcrm-frontend.vercel.app/api/v1/integrations/webhooks/razorpay/
```
Set `RAZORPAY_WEBHOOK_SECRET` on Render. Captured payments appear in
`/finance/payments` and update invoice status automatically. Duplicate
deliveries are deduplicated by event id.

For other gateways (Stripe, PayU, etc.): use n8n's native trigger for
that provider → POST to `/api/v1/finance/payments/` with the matched
customer + invoice.

---

## 11. Outbound: CRM → n8n (for custom workflows)

When a lead is converted / invoice paid / etc., the CRM POSTs to any
URL you register at **Settings → Webhooks**. Body:
```json
{ "event": "invoice.paid", "data": { ... }, "at": "..." }
```
Signed with HMAC-SHA256 over the raw body, in `X-CCRM-Signature`.
Verify in n8n's **Webhook** trigger node with a **Code** node:
```javascript
const crypto = require('crypto');
const secret = $env.WEBHOOK_SECRET;
const mac = crypto.createHmac('sha256', secret).update($request.body).digest('hex');
if (mac !== $headers['x-ccrm-signature']) throw new Error('bad signature');
return items;
```

---

## Available outbound events

| Event | Fires when |
|---|---|
| `lead.created` | (future — add signal if needed) |
| `lead.assigned` | A lead is assigned to a salesperson |
| `lead.converted` | A lead is converted to customer |
| `customer.created` | A new customer row is created |
| `invoice.issued` | (future — add signal if needed) |
| `invoice.paid` | An invoice reaches PAID status |
| `payment.successful` | A successful payment is recorded |
| `payment.refunded` | A refund is recorded |
| `task.assigned` | (future — add signal if needed) |
| `task.completed` | A task is marked complete |
| `webinar.registration` | (future — add signal if needed) |
