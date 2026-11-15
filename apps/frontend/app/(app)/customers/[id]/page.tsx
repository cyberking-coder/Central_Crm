import { notFound } from "next/navigation";

import { apiGet } from "@/lib/api-server";
import { ConversationThread } from "@/components/conversation-thread";
import type { Customer, TimelineEvent } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function CustomerDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const customer = await apiGet<Customer>(`/customers/${params.id}/`);
  if (!customer.ok) {
    if (customer.status === 404) notFound();
    return (
      <p className="text-red-400">
        Failed to load customer: {customer.detail}
      </p>
    );
  }
  const timeline = await apiGet<TimelineEvent[]>(
    `/customers/${params.id}/timeline/`,
  );

  return (
    <div className="space-y-8">
      <header>
        <p className="text-xs uppercase tracking-widest text-muted">Customer</p>
        <h1 className="text-3xl font-semibold tracking-tight">
          {customer.data.full_name}
        </h1>
        <p className="mt-1 text-sm text-muted">
          {customer.data.phone || "—"} · {customer.data.email || "—"} ·{" "}
          <span className="capitalize">{customer.data.status}</span>
        </p>
      </header>

      <section className="grid grid-cols-2 gap-6">
        <div className="rounded-xl border border-border p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-muted">
            Profile
          </h2>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
            <dt className="text-muted">Source</dt>
            <dd>{customer.data.source_name ?? "—"}</dd>
            <dt className="text-muted">Assigned to</dt>
            <dd>{customer.data.assigned_to_name ?? "Unassigned"}</dd>
            <dt className="text-muted">Address</dt>
            <dd>{customer.data.address || "—"}</dd>
            <dt className="text-muted">Created</dt>
            <dd>{new Date(customer.data.created_at).toLocaleString()}</dd>
          </dl>
          {customer.data.notes && (
            <>
              <h3 className="mt-6 text-xs uppercase tracking-wide text-muted">
                Notes
              </h3>
              <p className="mt-1 whitespace-pre-wrap text-sm">
                {customer.data.notes}
              </p>
            </>
          )}
        </div>

        <div className="rounded-xl border border-border p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-muted">
            Timeline
          </h2>
          {timeline.ok && timeline.data.length > 0 ? (
            <ol className="space-y-3 text-sm">
              {timeline.data.map((e) => (
                <li key={e.id} className="flex gap-3">
                  <span className="text-muted">
                    {new Date(e.occurred_at).toLocaleString()}
                  </span>
                  <span>{e.summary}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-muted">No events yet.</p>
          )}
        </div>
      </section>

      <ConversationThread customerId={customer.data.id} />
    </div>
  );
}
