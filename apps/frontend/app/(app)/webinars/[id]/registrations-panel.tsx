"use client";

import { useEffect, useState, useTransition } from "react";

import { api } from "@/lib/api-client";
import type { WebinarRegistration } from "@/lib/types";

const ATTENDANCE_OPTIONS = [
  { value: "registered", label: "— no data —" },
  { value: "attended", label: "Attended" },
  { value: "partial", label: "Partially attended" },
  { value: "absent", label: "Absent" },
  { value: "cancelled", label: "Cancelled" },
];

export function RegistrationsPanel({ webinarId }: { webinarId: string }) {
  const [regs, setRegs] = useState<WebinarRegistration[]>([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  async function refresh() {
    const res = await api.get<WebinarRegistration[]>(
      `/webinars/${webinarId}/registrations/`,
    );
    if (res.ok) setRegs(res.data);
  }

  useEffect(() => {
    refresh();
    // refresh depends only on webinarId via its closure
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [webinarId]);

  function addRegistration(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    start(async () => {
      const res = await api.post(`/webinars/${webinarId}/register/`, {
        full_name: name,
        email,
        phone,
      });
      if (!res.ok) {
        setError(res.error);
        return;
      }
      setName("");
      setEmail("");
      setPhone("");
      refresh();
    });
  }

  async function updateAttendance(regId: string, attendanceId: string | null,
                                   status: string) {
    // Need to fetch the attendance id if not present.
    if (!attendanceId) return;
    await api.patch(`/webinars/attendance/${attendanceId}/`, { status });
    refresh();
  }

  async function withAttendanceId(reg: WebinarRegistration,
                                   fn: (attId: string) => Promise<void>) {
    // Fetch all attendance rows for this webinar and find the one linked to reg.
    const res = await api.get<{ count: number; results: Array<any> }>(
      `/webinars/attendance/?registration__webinar=${webinarId}`,
    );
    if (!res.ok) return;
    const row = res.data.results.find((a: any) => a.registration === reg.id);
    if (row) await fn(row.id);
    refresh();
  }

  return (
    <section className="grid grid-cols-2 gap-6">
      <div className="rounded-xl border border-border p-6">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">
          Register
        </h2>
        <form onSubmit={addRegistration} className="space-y-2 text-sm">
          <input
            required
            placeholder="Full name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-border bg-transparent px-3 py-2"
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-border bg-transparent px-3 py-2"
          />
          <input
            placeholder="Phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-md border border-border bg-transparent px-3 py-2"
          />
          {error && <p className="text-xs text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={pending || !name}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg disabled:opacity-50"
          >
            Add registration
          </button>
        </form>
      </div>

      <div className="rounded-xl border border-border p-6">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">
          Registrations ({regs.length})
        </h2>
        <ul className="divide-y divide-border text-sm">
          {regs.map((r) => (
            <li
              key={r.id}
              className="flex items-center justify-between gap-2 py-2"
            >
              <div>
                <p className="font-medium">{r.full_name}</p>
                <p className="text-xs text-muted">
                  {r.email || r.phone || "—"} · {r.status}
                </p>
              </div>
              <select
                defaultValue={r.attendance_status ?? "registered"}
                onChange={(e) =>
                  withAttendanceId(r, (attId) =>
                    api
                      .patch(`/webinars/attendance/${attId}/`, {
                        status: e.target.value,
                      })
                      .then(() => undefined),
                  )
                }
                className="rounded-md border border-border bg-bg px-2 py-1 text-xs"
              >
                {ATTENDANCE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </li>
          ))}
          {regs.length === 0 && (
            <li className="py-3 text-xs text-muted">No registrations.</li>
          )}
        </ul>
      </div>
    </section>
  );
}
