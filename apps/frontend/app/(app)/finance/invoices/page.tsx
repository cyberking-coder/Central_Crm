import Link from "next/link";

import { apiGet } from "@/lib/api-server";
import type { Invoice, Paginated } from "@/lib/types";

export const dynamic = "force-dynamic";

function statusClass(s: string): string {
  const map: Record<string, string> = {
    draft: "bg-border/40 text-muted",
    issued: "bg-amber-500/15 text-amber-400",
    partially_paid: "bg-indigo-500/15 text-indigo-400",
    paid: "bg-emerald-500/15 text-emerald-400",
    void: "bg-red-500/15 text-red-400",
  };
  return map[s] ?? "bg-border/40 text-muted";
}

export default async function InvoicesPage() {
  const result = await apiGet<Paginated<Invoice>>("/finance/invoices/");

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Invoices</h1>
          <p className="text-sm text-muted">
            {result.ok ? `${result.data.count} total` : "—"}
          </p>
        </div>
        <div className="flex gap-2">
          <a
            href="/api/v1/finance/invoices/export/"
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-border/30"
          >
            Export CSV
          </a>
          <Link
            href="/finance/invoices/new"
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg"
          >
            New invoice
          </Link>
        </div>
      </header>

      {!result.ok ? (
        <p className="text-red-400">Failed to load: {result.detail}</p>
      ) : (result.data.results ?? []).length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted">
          No invoices yet.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Number</th>
                <th className="px-4 py-3">Customer</th>
                <th className="px-4 py-3">Issued</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {result.data.results.map((i) => (
                <tr key={i.id} className="border-t border-border hover:bg-border/10">
                  <td className="px-4 py-3 font-mono text-xs">
                    <Link href={`/finance/invoices/${i.id}`} className="hover:underline">
                      {i.number}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{i.customer_name}</td>
                  <td className="px-4 py-3 text-muted">
                    {new Date(i.issued_date).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {i.currency} {i.total}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${statusClass(i.status)}`}>
                      {i.status.replace("_", " ")}
                    </span>
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
