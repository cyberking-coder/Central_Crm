import { WebhooksPanel } from "./webhooks-panel";

export const dynamic = "force-dynamic";

export default function WebhooksPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">
          Outbound webhooks
        </h1>
        <p className="text-sm text-muted">
          Send a signed POST to any URL when things happen in the CRM. Point
          n8n, Zapier, Make, or a bespoke script at the URL; use the secret
          to verify the <code>X-CCRM-Signature</code> HMAC-SHA256 header.
        </p>
      </header>
      <WebhooksPanel />
    </div>
  );
}
