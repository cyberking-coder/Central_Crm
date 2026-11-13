"use client";

import { useEffect, useState, useTransition } from "react";

import { api } from "@/lib/api-client";
import type { FollowUp, SalesActivity } from "@/lib/types";

const ACTIVITY_KINDS = [
  { value: "call_out", label: "Outgoing call" },
  { value: "call_in", label: "Incoming call" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "email", label: "Email" },
  { value: "meeting", label: "Meeting" },
  { value: "follow_up", label: "Follow-up" },
  { value: "other", label: "Other" },
];

type Paginated<T> = { count: number; results: T[] };

export function ActivityPanel({ leadId }: { leadId: string }) {
  const [activities, setActivities] = useState<SalesActivity[]>([]);
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [kind, setKind] = useState("call_out");
  const [outcome, setOutcome] = useState("");
  const [summary, setSummary] = useState("");
  const [fuDueAt, setFuDueAt] = useState("");
  const [fuSummary, setFuSummary] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  async function refresh() {
    const [a, f] = await Promise.all([
      api.get<Paginated<SalesActivity>>(`/sales/activities/?lead=${leadId}`),
      api.get<Paginated<FollowUp>>(`/sales/followups/?lead=${leadId}`),
    ]);
    if (a.ok) setActivities(a.data.results);
    if (f.ok) setFollowups(f.data.results);
  }

  useEffect(() => {
    refresh();
  }, [leadId]);

  function logActivity(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    start(async () => {
      const res = await api.post<SalesActivity>("/sales/activities/", {
        lead: leadId,
        kind,
        outcome,
        discussion_summary: summary,
      });
      if (!res.ok) {
        setError(res.error);
        return;
      }
      setOutcome("");
      setSummary("");
      refresh();
    });
  }

  function createFollowup(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    start(async () => {
      const res = await api.post<FollowUp>("/sales/followups/", {
        lead: leadId,
        due_at: new Date(fuDueAt).toISOString(),
        summary: fuSummary,
      });
      if (!res.ok) {
        setError(res.error);
        return;
      }
      setFuDueAt("");
      setFuSummary("");
      refresh();
    });
  }

  function completeFollowup(id: string) {
    start(async () => {
      await api.post(`/sales/followups/${id}/complete/`);
      refresh();
    });
  }

  return (
    <section className="grid grid-cols-2 gap-6">
      <div className="rounded-xl border border-border p-6">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">
          Log activity
        </h2>
        <form onSubmit={logActivity} className="space-y-2 text-sm">
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2"
          >
            {ACTIVITY_KINDS.map((k) => (
              <option key={k.value} value={k.value}>
                {k.label}
              </option>
            ))}
          </select>
          <input
            value={outcome}
            onChange={(e) => setOutcome(e.target.value)}
            placeholder="Outcome (short)"
            className="w-full rounded-md border border-border bg-transparent px-3 py-2"
          />
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Discussion summary…"
            rows={3}
            className="w-full rounded-md border border-border bg-transparent px-3 py-2"
          />
          <button
            type="submit"
            disabled={pending}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg"
          >
            Log
          </button>
        </form>

        <h3 className="mt-6 text-xs uppercase tracking-wide text-muted">
          Recent activity
        </h3>
        <ul className="mt-2 space-y-2 text-sm">
          {activities.slice(0, 10).map((a) => (
            <li key={a.id} className="rounded-md border border-border p-2">
              <div className="flex justify-between">
                <span className="font-medium">{a.kind_label}</span>
                <span className="text-xs text-muted">
                  {new Date(a.occurred_at).toLocaleString()}
                </span>
              </div>
              {a.outcome && <p className="text-xs text-muted">{a.outcome}</p>}
              {a.discussion_summary && (
                <p className="mt-1 whitespace-pre-wrap text-xs">
                  {a.discussion_summary}
                </p>
              )}
            </li>
          ))}
          {activities.length === 0 && (
            <li className="text-xs text-muted">No activity yet.</li>
          )}
        </ul>
      </div>

      <div className="rounded-xl border border-border p-6">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">
          Schedule follow-up
        </h2>
        <form onSubmit={createFollowup} className="space-y-2 text-sm">
          <input
            type="datetime-local"
            value={fuDueAt}
            onChange={(e) => setFuDueAt(e.target.value)}
            required
            className="w-full rounded-md border border-border bg-transparent px-3 py-2"
          />
          <input
            value={fuSummary}
            onChange={(e) => setFuSummary(e.target.value)}
            placeholder="What to do?"
            required
            className="w-full rounded-md border border-border bg-transparent px-3 py-2"
          />
          <button
            type="submit"
            disabled={pending || !fuDueAt || !fuSummary}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg disabled:opacity-50"
          >
            Schedule
          </button>
        </form>

        <h3 className="mt-6 text-xs uppercase tracking-wide text-muted">
          Open follow-ups
        </h3>
        <ul className="mt-2 space-y-2 text-sm">
          {followups
            .filter((f) => f.status === "open")
            .map((f) => (
              <li
                key={f.id}
                className="flex items-center justify-between rounded-md border border-border p-2"
              >
                <div>
                  <p className={f.is_overdue ? "font-medium text-red-400" : ""}>
                    {f.summary}
                  </p>
                  <p className="text-xs text-muted">
                    due {new Date(f.due_at).toLocaleString()}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => completeFollowup(f.id)}
                  disabled={pending}
                  className="rounded-md border border-border px-2 py-1 text-xs hover:bg-border/30"
                >
                  Done
                </button>
              </li>
            ))}
          {followups.filter((f) => f.status === "open").length === 0 && (
            <li className="text-xs text-muted">No open follow-ups.</li>
          )}
        </ul>
      </div>
      {error && <p className="col-span-2 text-sm text-red-400">{error}</p>}
    </section>
  );
}
