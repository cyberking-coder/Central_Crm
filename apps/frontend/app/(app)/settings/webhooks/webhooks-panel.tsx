"use client";

import { useEffect, useState, useTransition } from "react";

import { api } from "@/lib/api-client";

type Sub = {
  id: string;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
  failure_count: number;
  last_delivery_at: string | null;
  last_delivery_status: string;
  last_error: string;
  created_at: string;
};

type Payload = {
  available_events: { code: string; label: string }[];
  results: Sub[];
};

export function WebhooksPanel() {
  const [data, setData] = useState<Payload | null>(null);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [events, setEvents] = useState<string[]>([]);
  const [created, setCreated] = useState<Sub & { secret: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  async function load() {
    const r = await api.get<Payload>("/integrations/outbound-webhooks/");
    if (r.ok) setData(r.data);
  }

  useEffect(() => {
    load();
  }, []);

  function toggle(e: string) {
    setEvents((cur) =>
      cur.includes(e) ? cur.filter((x) => x !== e) : [...cur, e],
    );
  }

  function create(ev: React.FormEvent) {
    ev.preventDefault();
    setError(null);
    setCreated(null);
    start(async () => {
      const r = await api.post<Sub & { secret: string }>(
        "/integrations/outbound-webhooks/",
        { name, url, events },
      );
      if (!r.ok) {
        setError(r.error);
        return;
      }
      setCreated(r.data);
      setName("");
      setUrl("");
      setEvents([]);
      load();
    });
  }

  function remove(id: string) {
    if (!confirm("Delete this webhook subscription?")) return;
    start(async () => {
      await api.del(`/integrations/outbound-webhooks/${id}/`);
      load();
    });
  }

  if (!data) return <p className="text-sm text-muted">Loading…</p>;

  return (
    <div className="space-y-6">
      <form
        onSubmit={create}
        className="space-y-3 rounded-xl border border-border bg-panel p-5"
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <label className="space-y-1 text-sm">
            <span className="text-muted">Name</span>
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="n8n: notify-sales"
              className="w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus:border-primary"
            />
          </label>
          <label className="space-y-1 text-sm">
            <span className="text-muted">Target URL</span>
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://your-n8n.example.com/webhook/abcdef"
              className="w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus:border-primary"
            />
          </label>
        </div>

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
            Events
          </p>
          <div className="grid grid-cols-2 gap-1.5 md:grid-cols-3">
            {data.available_events.map((e) => (
              <label
                key={e.code}
                className="flex items-center gap-2 text-sm"
              >
                <input
                  type="checkbox"
                  checked={events.includes(e.code)}
                  onChange={() => toggle(e.code)}
                />
                <span>{e.label}</span>
                <code className="text-[10px] text-muted">{e.code}</code>
              </label>
            ))}
          </div>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="submit"
          disabled={pending || !name || !url || events.length === 0}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-fg disabled:opacity-60"
        >
          {pending ? "Creating…" : "Create subscription"}
        </button>
      </form>

      {created && (
        <div className="rounded-xl border border-success/40 bg-success/10 p-4 text-sm">
          <p className="mb-1 font-medium text-success">
            Subscription created — save this secret
          </p>
          <p className="mb-2 text-xs text-fg/70">
            Use it to verify the X-CCRM-Signature HMAC-SHA256 header on
            incoming POSTs. It won't be shown again.
          </p>
          <code className="block overflow-auto rounded-md bg-black/40 px-3 py-2 font-mono text-xs">
            {created.secret}
          </code>
          <button
            type="button"
            onClick={() => setCreated(null)}
            className="mt-3 text-xs text-muted hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-border bg-panel">
        <table className="w-full text-sm">
          <thead className="bg-border/30 text-left text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">URL</th>
              <th className="px-4 py-3">Events</th>
              <th className="px-4 py-3">Last delivery</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {data.results.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted">
                  No subscriptions yet.
                </td>
              </tr>
            ) : (
              data.results.map((s) => (
                <tr key={s.id} className="border-t border-border">
                  <td className="px-4 py-3">
                    <p className="font-medium">{s.name}</p>
                    <p className="text-xs text-muted">
                      {s.is_active ? "active" : "disabled"}
                      {s.failure_count > 0 && (
                        <span className="ml-2 text-danger">
                          {s.failure_count} consecutive failures
                        </span>
                      )}
                    </p>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted break-all">
                    {s.url}
                  </td>
                  <td className="px-4 py-3 text-xs">
                    {s.events.join(", ")}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">
                    {s.last_delivery_at
                      ? `${new Date(s.last_delivery_at).toLocaleString()} · ${s.last_delivery_status}`
                      : "never"}
                    {s.last_error && (
                      <p className="text-danger">{s.last_error}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => remove(s.id)}
                      className="rounded-md border border-border px-2 py-1 text-xs text-danger hover:bg-border/30"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
