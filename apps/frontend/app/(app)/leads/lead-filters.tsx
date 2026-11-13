"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { LEAD_STATUSES } from "@/lib/types";

export function LeadFilters() {
  const router = useRouter();
  const params = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const [status, setStatus] = useState(params.get("status") ?? "");

  function apply(next: { q?: string; status?: string }) {
    const sp = new URLSearchParams();
    const nq = next.q ?? q;
    const ns = next.status ?? status;
    if (nq) sp.set("q", nq);
    if (ns) sp.set("status", ns);
    router.push(`/leads?${sp.toString()}`);
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        apply({});
      }}
      className="flex flex-wrap items-center gap-3"
    >
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search name, email, phone…"
        className="w-64 rounded-md border border-border bg-transparent px-3 py-1.5 text-sm outline-none focus:border-primary"
      />
      <select
        value={status}
        onChange={(e) => {
          setStatus(e.target.value);
          apply({ status: e.target.value });
        }}
        className="rounded-md border border-border bg-bg px-3 py-1.5 text-sm"
      >
        <option value="">All statuses</option>
        {LEAD_STATUSES.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
      <button
        type="submit"
        className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-border/30"
      >
        Apply
      </button>
    </form>
  );
}
