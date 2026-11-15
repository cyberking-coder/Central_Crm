import { AdsDashboard } from "./ads-dashboard";

export const dynamic = "force-dynamic";

export default function AdsPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Ads</h1>
        <p className="text-sm text-muted">
          Live spend, clicks and conversions per campaign. Data is pushed
          in by n8n (Meta / Google Ads scheduled polls) — see the{" "}
          <a href="/settings/integrations" className="text-primary underline">
            Integrations guide
          </a>
          .
        </p>
      </header>
      <AdsDashboard />
    </div>
  );
}
