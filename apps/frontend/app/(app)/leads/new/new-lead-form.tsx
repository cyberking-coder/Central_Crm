"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { api } from "@/lib/api-client";
import type { Lead, LeadSource } from "@/lib/types";

export function NewLeadForm({ sources }: { sources: LeadSource[] }) {
  const router = useRouter();
  const [form, setForm] = useState({
    full_name: "",
    phone: "",
    email: "",
    source: "",
    interested_product: "",
    priority: "medium",
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<Lead[]>([]);
  const [pending, start] = useTransition();

  async function checkDuplicates() {
    if (!form.phone && !form.email) return;
    const qs = new URLSearchParams();
    if (form.phone) qs.set("phone", form.phone);
    if (form.email) qs.set("email", form.email);
    const res = await api.get<Lead[]>(`/leads/duplicates/?${qs.toString()}`);
    setDuplicates(res.ok ? res.data : []);
  }

  function update<K extends keyof typeof form>(k: K, v: string) {
    setForm({ ...form, [k]: v });
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    start(async () => {
      const payload: Record<string, unknown> = { ...form };
      if (!payload.source) delete payload.source;
      const res = await api.post<Lead>("/leads/", payload);
      if (!res.ok) {
        setError(res.error);
        return;
      }
      router.push(`/leads/${res.data.id}`);
      router.refresh();
    });
  }

  return (
    <form onSubmit={submit} className="max-w-2xl space-y-4" noValidate>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Full name *">
          <input
            required
            value={form.full_name}
            onChange={(e) => update("full_name", e.target.value)}
            className={inputCls}
          />
        </Field>
        <Field label="Priority">
          <select
            value={form.priority}
            onChange={(e) => update("priority", e.target.value)}
            className={inputCls}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </Field>
        <Field label="Phone">
          <input
            value={form.phone}
            onChange={(e) => update("phone", e.target.value)}
            onBlur={checkDuplicates}
            className={inputCls}
          />
        </Field>
        <Field label="Email">
          <input
            type="email"
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
            onBlur={checkDuplicates}
            className={inputCls}
          />
        </Field>
        <Field label="Source">
          <select
            value={form.source}
            onChange={(e) => update("source", e.target.value)}
            className={inputCls}
          >
            <option value="">—</option>
            {sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Interested product">
          <input
            value={form.interested_product}
            onChange={(e) => update("interested_product", e.target.value)}
            className={inputCls}
          />
        </Field>
      </div>

      <Field label="Notes">
        <textarea
          rows={4}
          value={form.notes}
          onChange={(e) => update("notes", e.target.value)}
          className={inputCls}
        />
      </Field>

      {duplicates.length > 0 && (
        <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
          <p className="mb-1 font-medium text-amber-300">
            {duplicates.length} possible duplicate
            {duplicates.length > 1 ? "s" : ""}
          </p>
          <ul className="list-disc space-y-0.5 pl-5 text-amber-200/90">
            {duplicates.slice(0, 5).map((d) => (
              <li key={d.id}>
                <a href={`/leads/${d.id}`} className="underline">
                  {d.full_name}
                </a>{" "}
                · {d.phone || d.email} · {d.status}
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-fg disabled:opacity-60"
        >
          {pending ? "Saving…" : "Create lead"}
        </button>
      </div>
    </form>
  );
}

const inputCls =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus:border-primary";

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1 text-sm">
      <span className="text-muted">{label}</span>
      {children}
    </label>
  );
}
