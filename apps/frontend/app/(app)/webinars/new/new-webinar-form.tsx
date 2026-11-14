"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { api } from "@/lib/api-client";
import type { Webinar } from "@/lib/types";

const input =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus:border-primary";

export function NewWebinarForm() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: "",
    description: "",
    start_at: "",
    end_at: "",
    platform: "",
    registration_url: "",
    registration_limit: "0",
  });
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  function set<K extends keyof typeof form>(k: K, v: string) {
    setForm({ ...form, [k]: v });
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    start(async () => {
      const res = await api.post<Webinar>("/webinars/", {
        ...form,
        start_at: new Date(form.start_at).toISOString(),
        end_at: new Date(form.end_at).toISOString(),
        registration_limit: Number(form.registration_limit) || 0,
      });
      if (!res.ok) {
        setError(res.error);
        return;
      }
      router.push(`/webinars/${res.data.id}`);
      router.refresh();
    });
  }

  return (
    <form onSubmit={submit} className="max-w-2xl space-y-4">
      <label className="block space-y-1 text-sm">
        <span className="text-muted">Title *</span>
        <input
          required
          value={form.title}
          onChange={(e) => set("title", e.target.value)}
          className={input}
        />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="text-muted">Description</span>
        <textarea
          rows={3}
          value={form.description}
          onChange={(e) => set("description", e.target.value)}
          className={input}
        />
      </label>
      <div className="grid grid-cols-2 gap-4">
        <label className="block space-y-1 text-sm">
          <span className="text-muted">Start *</span>
          <input
            type="datetime-local"
            required
            value={form.start_at}
            onChange={(e) => set("start_at", e.target.value)}
            className={input}
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-muted">End *</span>
          <input
            type="datetime-local"
            required
            value={form.end_at}
            onChange={(e) => set("end_at", e.target.value)}
            className={input}
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-muted">Platform</span>
          <input
            value={form.platform}
            onChange={(e) => set("platform", e.target.value)}
            placeholder="Zoom, Meet, in-person…"
            className={input}
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-muted">Capacity (0 = unlimited)</span>
          <input
            type="number"
            min={0}
            value={form.registration_limit}
            onChange={(e) => set("registration_limit", e.target.value)}
            className={input}
          />
        </label>
      </div>
      <label className="block space-y-1 text-sm">
        <span className="text-muted">Registration URL</span>
        <input
          value={form.registration_url}
          onChange={(e) => set("registration_url", e.target.value)}
          placeholder="https://…"
          className={input}
        />
      </label>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-fg disabled:opacity-60"
      >
        {pending ? "Saving…" : "Create webinar"}
      </button>
    </form>
  );
}
