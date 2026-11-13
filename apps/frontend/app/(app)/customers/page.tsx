import Link from "next/link";

import { apiGet } from "@/lib/api-server";
import type { Customer, Paginated } from "@/lib/types";

export const dynamic = "force-dynamic";

type SearchParams = { [key: string]: string | string[] | undefined };

export default async function CustomersPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const qs = new URLSearchParams();
  if (searchParams.q) qs.set("search", String(searchParams.q));
  const result = await apiGet<Paginated<Customer>>(
    `/customers/?${qs.toString()}`,
  );

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Customers</h1>
          <p className="text-sm text-muted">
            {result.ok ? `${result.data.count} total` : "—"}
          </p>
        </div>
        <a
          href="/api/v1/customers/export/"
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-border/30"
        >
          Export CSV
        </a>
      </header>

      {!result.ok ? (
        <p className="text-sm text-red-400">
          Failed to load: {result.detail}
        </p>
      ) : result.data.results.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted">
          No customers yet. Convert a qualified lead from the Leads page.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Contact</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Assigned</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {result.data.results.map((c) => (
                <tr
                  key={c.id}
                  className="border-t border-border hover:bg-border/10"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/customers/${c.id}`}
                      className="font-medium hover:underline"
                    >
                      {c.full_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {c.phone || c.email || "—"}
                  </td>
                  <td className="px-4 py-3 capitalize">{c.status}</td>
                  <td className="px-4 py-3 text-muted">
                    {c.assigned_to_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {c.source_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {new Date(c.created_at).toLocaleDateString()}
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
