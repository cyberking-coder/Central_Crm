import { apiGet } from "@/lib/api-server";
import { DateRange } from "@/components/date-range";

export const dynamic = "force-dynamic";

type Row = {
  source: string;
  leads: number;
  qualified: number;
  converted: number;
  conversion_pct: number;
  attributed_revenue: string;
};
type Payload = { from: string; to: string; rows: Row[] };

export default async function SourceReport({
  searchParams,
}: {
  searchParams: { from?: string; to?: string };
}) {
  const qs = new URLSearchParams();
  if (searchParams.from) qs.set("from", searchParams.from);
  if (searchParams.to) qs.set("to", searchParams.to);
  const result = await apiGet<Payload>(
    `/analytics/reports/sources/?${qs.toString()}`,
  );

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            Lead sources
          </h1>
          <p className="text-sm text-muted">
            {result.ok ? `${result.data.from} → ${result.data.to}` : "—"}
          </p>
        </div>
        <div className="flex items-end gap-2">
          <DateRange basePath="/reports/sources" />
          <a
            href={`/api/v1/analytics/reports/sources/export/?${qs.toString()}`}
            className="rounded-md border border-border px-3 py-1 text-sm hover:bg-border/30"
          >
            Export CSV
          </a>
        </div>
      </header>

      {!result.ok ? (
        <p className="text-red-400">Failed: {result.detail}</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3 text-right">Leads</th>
                <th className="px-4 py-3 text-right">Qualified</th>
                <th className="px-4 py-3 text-right">Converted</th>
                <th className="px-4 py-3 text-right">Conv %</th>
                <th className="px-4 py-3 text-right">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {result.data.rows.map((r) => (
                <tr key={r.source} className="border-t border-border">
                  <td className="px-4 py-3">{r.source}</td>
                  <td className="px-4 py-3 text-right font-mono">{r.leads}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.qualified}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.converted}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.conversion_pct}%
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.attributed_revenue}
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
