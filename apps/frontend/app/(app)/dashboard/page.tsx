import Link from "next/link";

import { apiGet } from "@/lib/api-server";
import { getMe } from "@/lib/auth-server";
import { DashboardCharts } from "./dashboard-charts";

export const dynamic = "force-dynamic";

type TodayPayload = {
  date: string;
  timezone: string;
  leads_received: number;
  leads_assigned: number;
  leads_awaiting_assignment: number;
  calls_logged: number;
  activities_logged: number;
  followups_due_today: number;
  followups_overdue: number;
  customers_converted: number;
  tasks_overdue: number;
  tasks_completed: number;
  gross_collections: string;
  refunds: string;
  net_collections: string;
  outstanding_invoices: string;
  pending_payments: string;
};

type WeeklyPayload = {
  week_start: string;
  week_end: string;
  leads_received: number;
  leads_assigned: number;
  customers_converted: number;
  activities_logged: number;
  tasks_completed: number;
  leads_by_source: { source: string; count: number }[];
};

type LeaderboardRow = {
  employee_id: string;
  employee_name: string;
  activities: number;
  conversions: number;
};

export default async function DashboardPage() {
  const me = (await getMe())!;
  const canSeeReports =
    me.permissions.includes("*") || me.permissions.includes("reports.read");

  if (!canSeeReports) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-muted">
          You don't have report access. Reach out to your admin if you need
          it.
        </p>
      </div>
    );
  }

  const [today, weekly, leaderboard] = await Promise.all([
    apiGet<TodayPayload>("/analytics/dashboard/today/"),
    apiGet<WeeklyPayload>("/analytics/dashboard/weekly/"),
    apiGet<LeaderboardRow[]>("/analytics/leaderboard/"),
  ]);

  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted">
          {today.ok
            ? `${new Date(today.data.date).toLocaleDateString(undefined, {
                weekday: "long",
                day: "numeric",
                month: "long",
              })} · ${today.data.timezone}`
            : "—"}
        </p>
      </header>

      {canSeeReports && <DashboardCharts />}

      {today.ok ? (
        <section>
          <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted">
            Today
          </h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Kpi
              label="Leads received"
              value={today.data.leads_received}
              href="/leads"
            />
            <Kpi
              label="Leads assigned"
              value={today.data.leads_assigned}
              href="/leads?status=assigned"
            />
            <Kpi
              label="Awaiting assignment"
              value={today.data.leads_awaiting_assignment}
              href="/leads?status=unassigned"
              accent={today.data.leads_awaiting_assignment > 0 ? "amber" : undefined}
            />
            <Kpi
              label="Customers converted"
              value={today.data.customers_converted}
              href="/customers"
            />
            <Kpi label="Calls logged" value={today.data.calls_logged} />
            <Kpi label="Activities" value={today.data.activities_logged} />
            <Kpi
              label="Follow-ups due"
              value={today.data.followups_due_today}
            />
            <Kpi
              label="Follow-ups overdue"
              value={today.data.followups_overdue}
              accent={today.data.followups_overdue > 0 ? "red" : undefined}
            />
            <Kpi
              label="Tasks overdue"
              value={today.data.tasks_overdue}
              href="/tasks?scope=overdue"
              accent={today.data.tasks_overdue > 0 ? "red" : undefined}
            />
            <Kpi
              label="Tasks completed"
              value={today.data.tasks_completed}
            />
          </div>

          {me.permissions.some(
            (p) => p === "*" || p === "finance.read",
          ) && (
            <>
              <h3 className="mb-3 mt-6 text-xs font-medium uppercase tracking-wide text-muted">
                Today — Finance
              </h3>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
                <MoneyKpi label="Gross collected" value={today.data.gross_collections} />
                <MoneyKpi label="Refunds" value={today.data.refunds} />
                <MoneyKpi label="Net collected" value={today.data.net_collections} />
                <MoneyKpi
                  label="Outstanding"
                  value={today.data.outstanding_invoices}
                  href="/finance/invoices?status=issued"
                />
                <MoneyKpi label="Pending" value={today.data.pending_payments} />
              </div>
            </>
          )}
        </section>
      ) : (
        <p className="text-red-400">
          Today's dashboard failed to load: {today.detail}
        </p>
      )}

      {weekly.ok && (
        <section>
          <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted">
            This week · {weekly.data.week_start} → {weekly.data.week_end}
          </h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <Kpi label="Leads" value={weekly.data.leads_received} />
            <Kpi label="Assigned" value={weekly.data.leads_assigned} />
            <Kpi label="Converted" value={weekly.data.customers_converted} />
            <Kpi label="Activities" value={weekly.data.activities_logged} />
            <Kpi label="Tasks done" value={weekly.data.tasks_completed} />
          </div>

          {weekly.data.leads_by_source.length > 0 && (
            <div className="mt-6 rounded-xl border border-border p-6">
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted">
                Leads by source
              </h3>
              <ul className="space-y-1 text-sm">
                {weekly.data.leads_by_source.map((row) => (
                  <li
                    key={row.source}
                    className="flex items-center justify-between"
                  >
                    <span>{row.source}</span>
                    <span className="font-mono text-muted">{row.count}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {leaderboard.ok && leaderboard.data.length > 0 && (
        <section>
          <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted">
            Salesperson leaderboard — this week
          </h2>
          <div className="overflow-hidden rounded-xl border border-border">
            <table className="w-full text-sm">
              <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Salesperson</th>
                  <th className="px-4 py-3 text-right">Activities</th>
                  <th className="px-4 py-3 text-right">Conversions</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.data.map((r, i) => (
                  <tr
                    key={r.employee_id}
                    className="border-t border-border hover:bg-border/10"
                  >
                    <td className="px-4 py-3 text-muted">{i + 1}</td>
                    <td className="px-4 py-3 font-medium">
                      {r.employee_name}
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      {r.activities}
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      {r.conversions}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

function Kpi({
  label,
  value,
  href,
  accent,
}: {
  label: string;
  value: number;
  href?: string;
  accent?: "red" | "amber";
}) {
  const accentCls =
    accent === "red"
      ? "border-danger/40"
      : accent === "amber"
        ? "border-warn/40"
        : "border-border";
  const valueCls =
    accent === "red"
      ? "text-danger"
      : accent === "amber"
        ? "text-warn"
        : "";

  const content = (
    <div
      className={`rounded-xl border bg-panel p-5 shadow-sm transition hover:border-primary/40 hover:shadow ${accentCls}`}
    >
      <p className={`text-3xl font-semibold tabular-nums ${valueCls}`}>
        {value}
      </p>
      <p className="mt-1 text-xs uppercase tracking-wide text-muted">
        {label}
      </p>
    </div>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}

function MoneyKpi({
  label,
  value,
  href,
}: {
  label: string;
  value: string;
  href?: string;
}) {
  const content = (
    <div className="rounded-xl border border-border bg-panel p-5 shadow-sm transition hover:border-primary/40 hover:shadow">
      <p className="text-2xl font-semibold tabular-nums">{value}</p>
      <p className="mt-1 text-xs uppercase tracking-wide text-muted">{label}</p>
    </div>
  );
  return href ? <Link href={href}>{content}</Link> : content;
}
