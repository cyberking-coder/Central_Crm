import { notFound } from "next/navigation";

import { apiGet } from "@/lib/api-server";
import type { Webinar, WebinarStats } from "@/lib/types";
import { RegistrationsPanel } from "./registrations-panel";

export const dynamic = "force-dynamic";

export default async function WebinarDetail({
  params,
}: {
  params: { id: string };
}) {
  const [webinar, stats] = await Promise.all([
    apiGet<Webinar>(`/webinars/${params.id}/`),
    apiGet<WebinarStats>(`/webinars/${params.id}/stats/`),
  ]);

  if (!webinar.ok) {
    if (webinar.status === 404) notFound();
    return <p className="text-red-400">Failed to load: {webinar.detail}</p>;
  }

  return (
    <div className="space-y-8">
      <header>
        <p className="text-xs uppercase tracking-widest text-muted">Webinar</p>
        <h1 className="text-3xl font-semibold tracking-tight">
          {webinar.data.title}
        </h1>
        <p className="mt-1 text-sm text-muted">
          {new Date(webinar.data.start_at).toLocaleString()} →{" "}
          {new Date(webinar.data.end_at).toLocaleString()} ·{" "}
          <span className="capitalize">{webinar.data.status}</span>
        </p>
      </header>

      {stats.ok && (
        <section className="grid grid-cols-2 gap-3 md:grid-cols-5">
          <Stat label="Registered" value={stats.data.registrations_total} />
          <Stat label="Eligible" value={stats.data.registrations_eligible} />
          <Stat label="Attended" value={stats.data.attended} />
          <Stat label="Absent" value={stats.data.absent} />
          <Stat
            label="Attendance %"
            value={`${stats.data.attendance_rate_pct}`}
          />
        </section>
      )}

      {webinar.data.description && (
        <section className="rounded-xl border border-border p-6 text-sm whitespace-pre-wrap">
          {webinar.data.description}
        </section>
      )}

      <RegistrationsPanel webinarId={webinar.data.id} />
    </div>
  );
}

function Stat({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div className="rounded-xl border border-border p-5">
      <p className="text-2xl font-semibold tabular-nums">{value}</p>
      <p className="mt-1 text-xs uppercase tracking-wide text-muted">{label}</p>
    </div>
  );
}
