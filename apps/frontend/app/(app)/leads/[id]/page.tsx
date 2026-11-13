import Link from "next/link";
import { notFound } from "next/navigation";

import { apiGet } from "@/lib/api-server";
import type { Lead } from "@/lib/types";
import { LeadActions } from "./lead-actions";

export const dynamic = "force-dynamic";

type History = {
  assignments: Array<{
    id: string;
    to_employee_name: string | null;
    from_employee_name: string | null;
    assigned_by_email: string | null;
    reason: string;
    assigned_at: string;
  }>;
  statuses: Array<{
    id: string;
    from_status: string;
    to_status: string;
    changed_at: string;
  }>;
};

export default async function LeadDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const lead = await apiGet<Lead>(`/leads/${params.id}/`);
  if (!lead.ok) {
    if (lead.status === 404) notFound();
    return <p className="text-red-400">Failed to load lead: {lead.detail}</p>;
  }
  const history = await apiGet<History>(`/leads/${params.id}/history/`);

  return (
    <div className="space-y-8">
      <header className="flex items-start justify-between gap-6">
        <div>
          <p className="text-xs uppercase tracking-widest text-muted">Lead</p>
          <h1 className="text-3xl font-semibold tracking-tight">
            {lead.data.full_name}
          </h1>
          <p className="mt-1 text-sm text-muted">
            {lead.data.phone || "—"} · {lead.data.email || "—"} ·{" "}
            <span className="capitalize">{lead.data.status}</span>
          </p>
        </div>
        <LeadActions lead={lead.data} />
      </header>

      <section className="grid grid-cols-2 gap-6">
        <div className="rounded-xl border border-border p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-muted">
            Details
          </h2>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
            <dt className="text-muted">Source</dt>
            <dd>{lead.data.source_name ?? "—"}</dd>
            <dt className="text-muted">Campaign</dt>
            <dd>{lead.data.campaign_name ?? "—"}</dd>
            <dt className="text-muted">Interested in</dt>
            <dd>{lead.data.interested_product || "—"}</dd>
            <dt className="text-muted">Priority</dt>
            <dd className="capitalize">{lead.data.priority}</dd>
            <dt className="text-muted">Assigned to</dt>
            <dd>{lead.data.assigned_to_name ?? "Unassigned"}</dd>
            <dt className="text-muted">Next follow-up</dt>
            <dd>
              {lead.data.next_followup_at
                ? new Date(lead.data.next_followup_at).toLocaleString()
                : "—"}
            </dd>
            <dt className="text-muted">Created</dt>
            <dd>{new Date(lead.data.created_at).toLocaleString()}</dd>
          </dl>
          {lead.data.notes && (
            <>
              <h3 className="mt-6 text-xs uppercase tracking-wide text-muted">
                Notes
              </h3>
              <p className="mt-1 whitespace-pre-wrap text-sm">
                {lead.data.notes}
              </p>
            </>
          )}
          {lead.data.converted_customer && (
            <div className="mt-6 rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm">
              Converted →{" "}
              <Link
                href={`/customers/${lead.data.converted_customer}`}
                className="text-emerald-300 underline"
              >
                View customer
              </Link>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-border p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-muted">
            History
          </h2>
          {history.ok ? (
            <ol className="space-y-3 text-sm">
              {history.data.statuses.map((s) => (
                <li key={s.id} className="flex gap-3">
                  <span className="text-muted">
                    {new Date(s.changed_at).toLocaleString()}
                  </span>
                  <span>
                    status: {s.from_status || "—"} → <b>{s.to_status}</b>
                  </span>
                </li>
              ))}
              {history.data.assignments.map((a) => (
                <li key={a.id} className="flex gap-3">
                  <span className="text-muted">
                    {new Date(a.assigned_at).toLocaleString()}
                  </span>
                  <span>
                    assigned to{" "}
                    <b>{a.to_employee_name ?? "Unassigned"}</b>
                    {a.reason ? ` (${a.reason})` : ""}
                  </span>
                </li>
              ))}
              {history.data.statuses.length === 0 &&
                history.data.assignments.length === 0 && (
                  <li className="text-muted">No history yet.</li>
                )}
            </ol>
          ) : (
            <p className="text-sm text-red-400">
              Couldn't load history: {history.detail}
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
