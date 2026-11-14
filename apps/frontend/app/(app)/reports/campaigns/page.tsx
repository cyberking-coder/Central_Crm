import { apiGet } from "@/lib/api-server";
import { DateRange } from "@/components/date-range";

export const dynamic = "force-dynamic";

type Row = {
  campaign: string;
  source: string;
  leads: number;
  converted: number;
  spend: string;
  attributed_revenue: string;
  cost_per_lead: string | null;
  roi_pct: number | null;
};
type Payload = { from: string; to: string; rows: Row[] };

export default async function CampaignReport({
  searchParams,
}: {
  searchParams: { from?: string; to?: string };
}) {
  const qs = new URLSearchParams();
  if (searchParams.from) qs.set("from", searchParams.from);
  if (searchParams.to) qs.set("to", searchParams.to);
  const result = await apiGet<Payload>(
    `/analytics/reports/campaigns/?${qs.toString()}`,
  );

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Campaigns</h1>
          <p className="text-sm text-muted">
            {result.ok ? `${result.data.from} → ${result.data.to}` : "—"}
          </p>
        </div>
        <div className="flex items-end gap-2">
          <DateRange basePath="/reports/campaigns" />
          <a
            href={`/api/v1/analytics/reports/campaigns/export/?${qs.toString()}`}
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
                <th className="px-4 py-3">Campaign</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3 text-right">Leads</th>
                <th className="px-4 py-3 text-right">Converted</th>
                <th className="px-4 py-3 text-right">Spend</th>
                <th className="px-4 py-3 text-right">Revenue</th>
                <th className="px-4 py-3 text-right">CPL</th>
                <th className="px-4 py-3 text-right">ROI %</th>
              </tr>
            </thead>
            <tbody>
              {result.data.rows.map((r) => (
                <tr key={r.campaign} className="border-t border-border">
                  <td className="px-4 py-3 font-medium">{r.campaign}</td>
                  <td className="px-4 py-3 text-muted">{r.source}</td>
                  <td className="px-4 py-3 text-right font-mono">{r.leads}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.converted}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{r.spend}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.attributed_revenue}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.cost_per_lead ?? "—"}
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-mono ${
                      r.roi_pct !== null && r.roi_pct < 0
                        ? "text-red-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {r.roi_pct !== null ? `${r.roi_pct}%` : "—"}
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
