"use client";

import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "@/lib/api-client";

type Totals = {
  spend: string;
  impressions: number;
  clicks: number;
  conversions: number;
  cpc: string | null;
  cpa: string | null;
  ctr_pct: number | null;
};

type CampaignRow = {
  campaign_id: string;
  campaign: string;
  source: string;
  spend: string;
  impressions: number;
  clicks: number;
  conversions: number;
  currency: string;
  cpc: string | null;
  cpm: string | null;
  cpa: string | null;
  ctr_pct: number | null;
};

type DayRow = {
  date: string;
  spend: string;
  impressions: number;
  clicks: number;
  conversions: number;
};

type Payload = {
  from: string;
  to: string;
  totals: Totals;
  campaigns: CampaignRow[];
  days: DayRow[];
};

export function AdsDashboard() {
  const [data, setData] = useState<Payload | null>(null);

  async function load() {
    const r = await api.get<Payload>("/marketing/ad-dashboard/?days=30");
    if (r.ok) setData(r.data);
  }

  useEffect(() => {
    load();
    const iv = setInterval(load, 60_000);
    return () => clearInterval(iv);
  }, []);

  if (!data) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-24 animate-pulse rounded-xl border border-border bg-panel/50"
          />
        ))}
      </div>
    );
  }

  const spendSeries = data.days.map((d) => ({
    date: d.date,
    spend: Number(d.spend),
    clicks: d.clicks,
  }));

  const empty = data.campaigns.length === 0;

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Spend" value={data.totals.spend} />
        <Stat label="Impressions" value={fmtInt(data.totals.impressions)} />
        <Stat label="Clicks" value={fmtInt(data.totals.clicks)} />
        <Stat label="Conversions" value={fmtInt(data.totals.conversions)} />
        <Stat label="CPC" value={data.totals.cpc ?? "—"} />
        <Stat label="CPA" value={data.totals.cpa ?? "—"} />
        <Stat
          label="CTR"
          value={data.totals.ctr_pct !== null ? `${data.totals.ctr_pct}%` : "—"}
        />
        <Stat
          label="Period"
          value={`${data.from} → ${data.to}`}
          valueCls="text-sm"
        />
      </section>

      {empty ? (
        <div className="rounded-xl border border-dashed border-border bg-panel p-10 text-center text-sm text-muted">
          No ad metrics yet. Push some from n8n:
          <br />
          <code className="mt-2 inline-block rounded bg-border/40 px-2 py-1 text-xs">
            POST /api/v1/marketing/ad-metrics/
          </code>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Card title="Spend over time">
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart
                  data={spendSeries}
                  margin={{ top: 8, right: 8, left: -8, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="spendG" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: "hsl(var(--muted))" }}
                    tickFormatter={(v) => v.slice(5)}
                    stroke="hsl(var(--border))"
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "hsl(var(--muted))" }}
                    stroke="hsl(var(--border))"
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--panel))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(v: number) => v.toLocaleString()}
                  />
                  <Area
                    type="monotone"
                    dataKey="spend"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    fill="url(#spendG)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Clicks over time">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart
                  data={spendSeries}
                  margin={{ top: 8, right: 8, left: -8, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: "hsl(var(--muted))" }}
                    tickFormatter={(v) => v.slice(5)}
                    stroke="hsl(var(--border))"
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "hsl(var(--muted))" }}
                    stroke="hsl(var(--border))"
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--panel))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="clicks"
                    stroke="hsl(var(--accent))"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </div>

          <Card title="By campaign">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="pb-2 pl-1">Campaign</th>
                  <th className="pb-2">Source</th>
                  <th className="pb-2 text-right">Spend</th>
                  <th className="pb-2 text-right">Impr.</th>
                  <th className="pb-2 text-right">Clicks</th>
                  <th className="pb-2 text-right">CTR</th>
                  <th className="pb-2 text-right">CPC</th>
                  <th className="pb-2 text-right">Conv.</th>
                  <th className="pb-2 text-right">CPA</th>
                </tr>
              </thead>
              <tbody>
                {data.campaigns.map((c) => (
                  <tr key={c.campaign_id} className="border-t border-border">
                    <td className="py-2 pl-1 font-medium">{c.campaign}</td>
                    <td className="py-2 text-muted">{c.source}</td>
                    <td className="py-2 text-right font-mono">
                      {c.currency} {c.spend}
                    </td>
                    <td className="py-2 text-right font-mono">
                      {fmtInt(c.impressions)}
                    </td>
                    <td className="py-2 text-right font-mono">
                      {fmtInt(c.clicks)}
                    </td>
                    <td className="py-2 text-right font-mono">
                      {c.ctr_pct !== null ? `${c.ctr_pct}%` : "—"}
                    </td>
                    <td className="py-2 text-right font-mono">
                      {c.cpc ?? "—"}
                    </td>
                    <td className="py-2 text-right font-mono">
                      {fmtInt(c.conversions)}
                    </td>
                    <td className="py-2 text-right font-mono">
                      {c.cpa ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  );
}

function fmtInt(n: number): string {
  return n.toLocaleString();
}

function Stat({
  label,
  value,
  valueCls = "",
}: {
  label: string;
  value: string;
  valueCls?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-panel p-5 shadow-sm">
      <p className={`font-semibold tabular-nums ${valueCls || "text-2xl"}`}>
        {value}
      </p>
      <p className="mt-1 text-xs uppercase tracking-wide text-muted">{label}</p>
    </div>
  );
}

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border bg-panel p-5 shadow-sm">
      <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted">
        {title}
      </p>
      {children}
    </div>
  );
}
