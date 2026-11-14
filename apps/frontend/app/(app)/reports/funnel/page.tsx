import { apiGet } from "@/lib/api-server";
import { DateRange } from "@/components/date-range";

export const dynamic = "force-dynamic";

type Payload = {
  from: string;
  to: string;
  stages: {
    leads: number;
    contacted: number;
    qualified: number;
    converted: number;
    lost: number;
  };
};

export default async function FunnelReport({
  searchParams,
}: {
  searchParams: { from?: string; to?: string };
}) {
  const qs = new URLSearchParams();
  if (searchParams.from) qs.set("from", searchParams.from);
  if (searchParams.to) qs.set("to", searchParams.to);
  const result = await apiGet<Payload>(
    `/analytics/reports/funnel/?${qs.toString()}`,
  );

  if (!result.ok) {
    return (
      <p className="text-red-400">Failed to load: {result.detail}</p>
    );
  }

  const { stages } = result.data;
  const stageList: [string, number][] = [
    ["Leads", stages.leads],
    ["Contacted", stages.contacted],
    ["Qualified", stages.qualified],
    ["Converted", stages.converted],
  ];
  const maxVal = Math.max(1, ...stageList.map(([, v]) => v));

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            Conversion funnel
          </h1>
          <p className="text-sm text-muted">
            {result.data.from} → {result.data.to}
          </p>
        </div>
        <DateRange basePath="/reports/funnel" />
      </header>

      <section className="space-y-3">
        {stageList.map(([label, value]) => (
          <div key={label}>
            <div className="mb-1 flex justify-between text-sm">
              <span>{label}</span>
              <span className="font-mono text-muted">{value}</span>
            </div>
            <div className="h-6 overflow-hidden rounded-md bg-border/30">
              <div
                className="h-full bg-primary"
                style={{ width: `${(value / maxVal) * 100}%` }}
              />
            </div>
          </div>
        ))}
        <div className="pt-2 text-sm text-muted">
          Lost in range:{" "}
          <span className="font-mono text-red-400">{stages.lost}</span>
        </div>
      </section>
    </div>
  );
}
