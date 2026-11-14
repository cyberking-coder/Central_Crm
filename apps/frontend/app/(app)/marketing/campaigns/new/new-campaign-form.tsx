"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { api } from "@/lib/api-client";
import type { Campaign, LeadSource } from "@/lib/types";

const input =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus:border-primary";

export function NewCampaignForm({ sources }: { sources: LeadSource[] }) {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    source: "",
    utm_source: "",
    utm_medium: "",
    utm_campaign: "",
    spend: "0",
    currency: "INR",
    is_active: true,
  });
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  function set<K extends keyof typeof form>(k: K, v: string | boolean) {
    setForm({ ...form, [k]: v } as typeof form);
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    start(async () => {
      const res = await api.post<Campaign>("/campaigns/", form);
      if (!res.ok) {
        setError(res.error);
        return;
      }
      router.push("/marketing/campaigns");
      router.refresh();
    });
  }

  return (
    <form onSubmit={submit} className="max-w-2xl space-y-4">
      <label className="block space-y-1 text-sm">
        <span className="text-muted">Name *</span>
        <input
          required
          value={form.name}
          onChange={(e) => set("name", e.target.value)}
          className={input}
        />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="text-muted">Source *</span>
        <select
          required
          value={form.source}
          onChange={(e) => set("source", e.target.value)}
          className={input}
        >
          <option value="">—</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
      <div className="grid grid-cols-3 gap-4">
        <label className="block space-y-1 text-sm">
          <span className="text-muted">utm_source</span>
          <input
            value={form.utm_source}
            onChange={(e) => set("utm_source", e.target.value)}
            className={input}
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-muted">utm_medium</span>
          <input
            value={form.utm_medium}
            onChange={(e) => set("utm_medium", e.target.value)}
            className={input}
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-muted">utm_campaign</span>
          <input
            value={form.utm_campaign}
            onChange={(e) => set("utm_campaign", e.target.value)}
            className={input}
          />
        </label>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <label className="block space-y-1 text-sm">
          <span className="text-muted">Spend</span>
          <input
            type="number"
            min={0}
            step="0.01"
            value={form.spend}
            onChange={(e) => set("spend", e.target.value)}
            className={input}
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-muted">Currency</span>
          <input
            value={form.currency}
            onChange={(e) => set("currency", e.target.value.toUpperCase())}
            maxLength={3}
            className={input}
          />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => set("is_active", e.target.checked)}
          />
          <span>Active</span>
        </label>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <button
        type="submit"
        disabled={pending || !form.name || !form.source}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-fg disabled:opacity-60"
      >
        {pending ? "Saving…" : "Create campaign"}
      </button>
    </form>
  );
}
