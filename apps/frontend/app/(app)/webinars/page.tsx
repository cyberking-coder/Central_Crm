import Link from "next/link";

import { apiGet } from "@/lib/api-server";
import type { Paginated, Webinar } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function WebinarsPage() {
  const result = await apiGet<Paginated<Webinar>>("/webinars/");

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Webinars</h1>
          <p className="text-sm text-muted">
            {result.ok ? `${result.data.count} total` : "—"}
          </p>
        </div>
        <Link
          href="/webinars/new"
          className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg"
        >
          New webinar
        </Link>
      </header>

      {!result.ok ? (
        <p className="text-red-400">Failed to load: {result.detail}</p>
      ) : result.data.results.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted">
          No webinars yet.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Start</th>
                <th className="px-4 py-3">Host</th>
                <th className="px-4 py-3">Capacity</th>
              </tr>
            </thead>
            <tbody>
              {result.data.results.map((w) => (
                <tr key={w.id} className="border-t border-border hover:bg-border/10">
                  <td className="px-4 py-3">
                    <Link
                      href={`/webinars/${w.id}`}
                      className="font-medium hover:underline"
                    >
                      {w.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 capitalize">{w.status}</td>
                  <td className="px-4 py-3 text-muted">
                    {new Date(w.start_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {w.host_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {w.registration_limit === 0
                      ? "Unlimited"
                      : w.registration_limit}
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
