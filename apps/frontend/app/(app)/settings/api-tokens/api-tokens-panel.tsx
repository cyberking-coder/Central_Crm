"use client";

import { useEffect, useState, useTransition } from "react";

import { api } from "@/lib/api-client";

type Token = {
  id: string;
  name: string;
  prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
};

type CreatedToken = Token & { key: string };

export function ApiTokensPanel() {
  const [tokens, setTokens] = useState<Token[]>([]);
  const [name, setName] = useState("");
  const [created, setCreated] = useState<CreatedToken | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  async function load() {
    const res = await api.get<{ results: Token[] }>("/auth/tokens/");
    if (res.ok) setTokens(res.data.results);
  }

  useEffect(() => {
    load();
  }, []);

  function create(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreated(null);
    start(async () => {
      const res = await api.post<CreatedToken>("/auth/tokens/", { name });
      if (!res.ok) {
        setError(res.error);
        return;
      }
      setCreated(res.data);
      setName("");
      load();
    });
  }

  function revoke(id: string) {
    if (!confirm("Revoke this token? Any integration using it will stop working.")) {
      return;
    }
    start(async () => {
      await api.del(`/auth/tokens/${id}/`);
      load();
    });
  }

  function copy(text: string) {
    navigator.clipboard.writeText(text);
  }

  return (
    <div className="space-y-6">
      <form
        onSubmit={create}
        className="flex items-end gap-2 rounded-xl border border-border p-4"
      >
        <label className="flex-1 space-y-1 text-sm">
          <span className="text-muted">Token name</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. n8n-production"
            className="w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus:border-primary"
          />
        </label>
        <button
          type="submit"
          disabled={pending || !name}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-fg disabled:opacity-60"
        >
          {pending ? "Creating…" : "Create token"}
        </button>
      </form>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {created && (
        <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4">
          <p className="mb-2 text-sm font-medium text-emerald-300">
            New token: {created.name}
          </p>
          <p className="mb-2 text-xs text-emerald-200">
            Copy this now. It will not be shown again.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 overflow-auto rounded-md bg-black/40 px-3 py-2 font-mono text-xs">
              {created.key}
            </code>
            <button
              type="button"
              onClick={() => copy(created.key)}
              className="rounded-md border border-border px-3 py-2 text-xs hover:bg-border/30"
            >
              Copy
            </button>
          </div>
          <button
            type="button"
            onClick={() => setCreated(null)}
            className="mt-3 text-xs text-muted hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Prefix</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3">Last used</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {tokens.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted">
                  No tokens yet.
                </td>
              </tr>
            ) : (
              tokens.map((t) => (
                <tr key={t.id} className="border-t border-border">
                  <td className="px-4 py-3 font-medium">{t.name}</td>
                  <td className="px-4 py-3 font-mono text-xs text-muted">
                    {t.prefix}…
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {new Date(t.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {t.last_used_at
                      ? new Date(t.last_used_at).toLocaleString()
                      : "never"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => revoke(t.id)}
                      className="rounded-md border border-border px-2 py-1 text-xs text-red-400 hover:bg-border/30"
                    >
                      Revoke
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
