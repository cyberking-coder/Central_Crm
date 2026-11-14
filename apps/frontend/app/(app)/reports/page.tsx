import Link from "next/link";

export const dynamic = "force-dynamic";

const REPORTS = [
  { href: "/reports/sources", title: "Lead sources",
    body: "Volume, qualified, conversion, revenue per source." },
  { href: "/reports/campaigns", title: "Campaigns",
    body: "Leads, spend, CPL and ROI per campaign." },
  { href: "/reports/funnel", title: "Conversion funnel",
    body: "Lead → contacted → qualified → converted / lost." },
  { href: "/reports/departments", title: "Departments",
    body: "Activities, tasks completed, conversions per department." },
];

export default function ReportsHome() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Reports</h1>
        <p className="text-sm text-muted">
          Each report has a date filter and a CSV export.
        </p>
      </header>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {REPORTS.map((r) => (
          <Link key={r.href} href={r.href}
                className="block rounded-xl border border-border p-5 hover:bg-border/10">
            <p className="text-sm font-medium">{r.title}</p>
            <p className="mt-1 text-xs text-muted">{r.body}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
