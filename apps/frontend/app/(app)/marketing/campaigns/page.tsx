import Link from "next/link";

import { apiGet } from "@/lib/api-server";
import type { Campaign, Paginated } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function CampaignsPage() {
  const result = await apiGet<Paginated<Campaign>>("/campaigns/");

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Campaigns</h1>
          <p className="text-sm text-muted">
            {result.ok ? `${result.data.count} total` : "—"}
          </p>
        </div>
        <Link
          href="/marketing/campaigns/new"
          className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg"
        >
          New campaign
        </Link>
      </header>

      {!result.ok ? (
        <p className="text-red-400">Failed: {result.detail}</p>
      ) : (result.data.results ?? []).length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted">
          No campaigns yet.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">UTM campaign</th>
                <th className="px-4 py-3">Active</th>
                <th className="px-4 py-3 text-right">Spend</th>
              </tr>
            </thead>
            <tbody>
              {result.data.results.map((c) => (
                <tr key={c.id} className="border-t border-border hover:bg-border/10">
                  <td className="px-4 py-3 font-medium">{c.name}</td>
                  <td className="px-4 py-3 text-muted">{c.source_name}</td>
                  <td className="px-4 py-3 font-mono text-xs">{c.utm_campaign || "—"}</td>
                  <td className="px-4 py-3 text-muted">
                    {c.is_active ? "Yes" : "No"}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{c.spend}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
