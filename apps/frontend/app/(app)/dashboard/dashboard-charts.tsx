"use client";

import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "@/lib/api-client";

type LeadRow = { date: string; count: number };
type CollectionRow = {
  date: string;
  gross: string;
  refunds: string;
  net: string;
};
type Payload = {
  from: string;
  to: string;
  leads_per_day: LeadRow[];
  collections_per_day: CollectionRow[];
};

function fillMissingDays<T extends { date: string }>(
  rows: T[],
  from: string,
  to: string,
  blank: Omit<T, "date">,
): T[] {
  const byDate = new Map(rows.map((r) => [r.date, r]));
  const out: T[] = [];
  const start = new Date(from);
  const end = new Date(to);
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const key = d.toISOString().slice(0, 10);
    out.push(byDate.get(key) ?? ({ date: key, ...blank } as T));
  }
  return out;
}

export function DashboardCharts() {
  const [data, setData] = useState<Payload | null>(null);

  useEffect(() => {
    api.get<Payload>("/analytics/dashboard/charts/").then((r) => {
      if (r.ok) setData(r.data);
    });
  }, []);

  if (!data) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  const leads = fillMissingDays(data.leads_per_day, data.from, data.to, {
    count: 0,
  });
  const collections = fillMissingDays(
    data.collections_per_day,
    data.from,
    data.to,
    { gross: "0", refunds: "0", net: "0" },
  ).map((r) => ({
    date: r.date,
    net: Number(r.net),
    gross: Number(r.gross),
  }));

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <ChartCard title="Leads · last 30 days">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={leads} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
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
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                background: "hsl(var(--panel))",
                border: "1px solid hsl(var(--border))",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Net collections · last 30 days">
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={collections} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
            <defs>
              <linearGradient id="netFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--success))" stopOpacity={0.35} />
                <stop offset="100%" stopColor="hsl(var(--success))" stopOpacity={0} />
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
              dataKey="net"
              stroke="hsl(var(--success))"
              strokeWidth={2}
              fill="url(#netFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

function ChartCard({
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

function SkeletonCard() {
  return (
    <div className="h-[268px] animate-pulse rounded-xl border border-border bg-panel/50" />
  );
}
