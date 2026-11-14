"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

function iso(d: Date) {
  return d.toISOString().slice(0, 10);
}

export function DateRange({ basePath }: { basePath: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const today = new Date();
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - today.getDay() + 1); // Monday

  const [from, setFrom] = useState(params.get("from") ?? iso(startOfWeek));
  const [to, setTo] = useState(params.get("to") ?? iso(today));

  function apply() {
    const sp = new URLSearchParams();
    sp.set("from", from);
    sp.set("to", to);
    router.push(`${basePath}?${sp.toString()}`);
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        apply();
      }}
      className="flex flex-wrap items-center gap-2 text-sm"
    >
      <label className="text-muted">From</label>
      <input type="date" value={from} onChange={(e) => setFrom(e.target.value)}
             className="rounded-md border border-border bg-transparent px-2 py-1" />
      <label className="text-muted">To</label>
      <input type="date" value={to} onChange={(e) => setTo(e.target.value)}
             className="rounded-md border border-border bg-transparent px-2 py-1" />
      <button type="submit"
              className="rounded-md border border-border px-3 py-1 hover:bg-border/30">
        Apply
      </button>
    </form>
  );
}
