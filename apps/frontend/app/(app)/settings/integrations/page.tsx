import { apiGet } from "@/lib/api-server";

export const dynamic = "force-dynamic";

type Row = {
  name: string;
  label: string;
  enabled: boolean;
  configured: boolean;
  last_event_at: string | null;
  details: string;
};
type Payload = { integrations: Row[] };

export default async function IntegrationsPage() {
  const result = await apiGet<Payload>("/integrations/status/");

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Integrations</h1>
        <p className="text-sm text-muted">
          Secrets live in the backend environment; nothing editable here.
          Status reflects what&apos;s wired up on the server.
        </p>
      </header>

      {!result.ok ? (
        <p className="text-red-400">Failed: {result.detail}</p>
      ) : (
        <ul className="space-y-3">
          {result.data.integrations.map((r) => (
            <li
              key={r.name}
              className="flex items-start justify-between rounded-xl border border-border p-5"
            >
              <div>
                <p className="text-lg font-medium">{r.label}</p>
                <p className="text-sm text-muted">{r.details}</p>
                {r.last_event_at && (
                  <p className="mt-1 text-xs text-muted">
                    Last event: {new Date(r.last_event_at).toLocaleString()}
                  </p>
                )}
              </div>
              <div className="flex gap-3">
                <Pill label="configured" on={r.configured} />
                <Pill label="enabled" on={r.enabled} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Pill({ label, on }: { label: string; on: boolean }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs ${
        on
          ? "bg-emerald-500/15 text-emerald-300"
          : "bg-border/40 text-muted"
      }`}
    >
      {on ? "✓" : "—"} {label}
    </span>
  );
}
