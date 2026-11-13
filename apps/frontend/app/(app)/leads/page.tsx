import Link from "next/link";

import { apiGet } from "@/lib/api-server";
import type { Lead, Paginated } from "@/lib/types";
import { LeadFilters } from "./lead-filters";

export const dynamic = "force-dynamic";

type SearchParams = { [key: string]: string | string[] | undefined };

function statusClass(s: string): string {
  const map: Record<string, string> = {
    new: "bg-blue-500/15 text-blue-400",
    assigned: "bg-amber-500/15 text-amber-400",
    contacted: "bg-indigo-500/15 text-indigo-400",
    qualified: "bg-emerald-500/15 text-emerald-400",
    converted: "bg-emerald-600/15 text-emerald-500",
    lost: "bg-red-500/15 text-red-400",
  };
  return map[s] ?? "bg-border/40 text-muted";
}

export default async function LeadsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const qs = new URLSearchParams();
  if (searchParams.q) qs.set("search", String(searchParams.q));
  if (searchParams.status) qs.set("status", String(searchParams.status));
  if (searchParams.page) qs.set("page", String(searchParams.page));

  const result = await apiGet<Paginated<Lead>>(`/leads/?${qs.toString()}`);

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Leads</h1>
          <p className="text-sm text-muted">
            {result.ok ? `${result.data.count} total` : "—"}
          </p>
        </div>
        <div className="flex gap-2">
          <a
            href="/api/v1/leads/export/"
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-border/30"
          >
            Export CSV
          </a>
          <Link
            href="/leads/new"
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg"
          >
            New lead
          </Link>
        </div>
      </header>

      <LeadFilters />

      {!result.ok ? (
        <p className="text-sm text-red-400">
          Failed to load leads: {result.detail}
        </p>
      ) : result.data.results.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted">
          No leads match your filters.{" "}
          <Link href="/leads/new" className="text-primary underline">
            Create one
          </Link>
          .
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Contact</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Assigned</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {result.data.results.map((l) => (
                <tr
                  key={l.id}
                  className="border-t border-border hover:bg-border/10"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/leads/${l.id}`}
                      className="font-medium hover:underline"
                    >
                      {l.full_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {l.phone || l.email || "—"}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {l.source_name ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${statusClass(
                        l.status,
                      )}`}
                    >
                      {l.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {l.assigned_to_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {new Date(l.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
