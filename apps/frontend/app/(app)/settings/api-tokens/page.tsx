import { ApiTokensPanel } from "./api-tokens-panel";

export const dynamic = "force-dynamic";

export default function ApiTokensPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">API tokens</h1>
        <p className="text-sm text-muted">
          Create a token for each integration (n8n, Zapier, Make, custom
          script). Pass it as{" "}
          <code className="rounded bg-border/40 px-1 py-0.5 text-xs">
            Authorization: Bearer &lt;token&gt;
          </code>{" "}
          on any request to <code>/api/v1/</code>. Tokens have your full
          permissions — treat them like passwords.
        </p>
      </header>
      <ApiTokensPanel />
    </div>
  );
}
