"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { api } from "@/lib/api-client";
import type { Lead, LeadStatus } from "@/lib/types";
import { LEAD_STATUSES } from "@/lib/types";

const CONVERTIBLE_STATUSES: LeadStatus[] = [
  "qualified", "interested", "contacted", "assigned", "new",
];

export function LeadActions({ lead }: { lead: Lead }) {
  const router = useRouter();
  const [status, setStatus] = useState<string>(lead.status);
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function changeStatus(next: string) {
    setStatus(next);
    setError(null);
    start(async () => {
      const res = await api.patch<Lead>(`/leads/${lead.id}/`, { status: next });
      if (!res.ok) {
        setError(res.error);
        setStatus(lead.status);
        return;
      }
      router.refresh();
    });
  }

  function convert() {
    setError(null);
    start(async () => {
      const res = await api.post<{ customer_id: string }>(
        `/leads/${lead.id}/convert/`,
      );
      if (!res.ok) {
        setError(res.error);
        return;
      }
      router.push(`/customers/${res.data.customer_id}`);
    });
  }

  const canConvert =
    !lead.converted_customer &&
    CONVERTIBLE_STATUSES.includes(lead.status as LeadStatus);

  return (
    <div className="flex items-center gap-2">
      <select
        value={status}
        onChange={(e) => changeStatus(e.target.value)}
        disabled={pending || !!lead.converted_customer}
        className="rounded-md border border-border bg-bg px-3 py-1.5 text-sm"
      >
        {LEAD_STATUSES.map((s) => (
          <option key={s} value={s} disabled={s === "converted"}>
            {s}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={convert}
        disabled={pending || !canConvert}
        className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg disabled:opacity-50"
      >
        Convert to customer
      </button>
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  );
}
