import { apiGet } from "@/lib/api-server";
import { DateRange } from "@/components/date-range";

export const dynamic = "force-dynamic";

type Row = {
  department: string;
  activities: number;
  tasks_completed: number;
  conversions: number;
};
type Payload = { from: string; to: string; rows: Row[] };

export default async function DepartmentReport({
  searchParams,
}: {
  searchParams: { from?: string; to?: string };
}) {
  const qs = new URLSearchParams();
  if (searchParams.from) qs.set("from", searchParams.from);
  if (searchParams.to) qs.set("to", searchParams.to);
  const result = await apiGet<Payload>(
    `/analytics/reports/departments/?${qs.toString()}`,
  );

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Departments</h1>
          <p className="text-sm text-muted">
            {result.ok ? `${result.data.from} → ${result.data.to}` : "—"}
          </p>
        </div>
        <div className="flex items-end gap-2">
          <DateRange basePath="/reports/departments" />
          <a
            href={`/api/v1/analytics/reports/departments/export/?${qs.toString()}`}
            className="rounded-md border border-border px-3 py-1 text-sm hover:bg-border/30"
          >
            Export CSV
          </a>
        </div>
      </header>

      {!result.ok ? (
        <p className="text-red-400">Failed: {result.detail}</p>
      ) : result.data.rows.length === 0 ? (
        <p className="text-muted">
          No departments configured yet. Create them from Django admin.
        </p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Department</th>
                <th className="px-4 py-3 text-right">Activities</th>
                <th className="px-4 py-3 text-right">Tasks done</th>
                <th className="px-4 py-3 text-right">Conversions</th>
              </tr>
            </thead>
            <tbody>
              {result.data.rows.map((r) => (
                <tr key={r.department} className="border-t border-border">
                  <td className="px-4 py-3">{r.department}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.activities}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.tasks_completed}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {r.conversions}
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
