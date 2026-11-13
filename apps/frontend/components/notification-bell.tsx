"use client";

import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api-client";
import type { Notification } from "@/lib/types";

type Paginated<T> = { count: number; results: T[] };

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState<number>(0);
  const [items, setItems] = useState<Notification[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  async function refreshCount() {
    const res = await api.get<{ count: number }>(
      "/notifications/unread_count/",
    );
    if (res.ok) setUnread(res.data.count);
  }

  async function load() {
    const res = await api.get<Paginated<Notification>>("/notifications/");
    if (res.ok) setItems(res.data.results);
  }

  async function markAllRead() {
    await api.post("/notifications/mark_all_read/");
    await Promise.all([load(), refreshCount()]);
  }

  async function markRead(id: string) {
    await api.post(`/notifications/${id}/mark_read/`);
    await Promise.all([load(), refreshCount()]);
  }

  useEffect(() => {
    refreshCount();
    const iv = setInterval(refreshCount, 30_000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    if (open) load();
  }, [open]);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-md border border-border px-3 py-1.5 text-sm"
        aria-label={`${unread} unread notifications`}
      >
        🔔{unread > 0 && (
          <span className="ml-1 rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-semibold text-primary-fg">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 top-full z-20 mt-2 w-80 rounded-xl border border-border bg-bg shadow-lg">
          <div className="flex items-center justify-between border-b border-border px-3 py-2 text-xs">
            <span className="text-muted">Notifications</span>
            <button
              type="button"
              onClick={markAllRead}
              className="text-primary hover:underline"
            >
              Mark all read
            </button>
          </div>
          <ul className="max-h-80 divide-y divide-border overflow-auto text-sm">
            {items.length === 0 ? (
              <li className="px-3 py-4 text-center text-muted">
                No notifications.
              </li>
            ) : (
              items.map((n) => (
                <li
                  key={n.id}
                  className={`px-3 py-2 ${n.is_read ? "opacity-60" : ""}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-medium">{n.title}</p>
                      {n.body && (
                        <p className="text-xs text-muted">{n.body}</p>
                      )}
                      <p className="mt-1 text-[10px] uppercase tracking-wide text-muted">
                        {new Date(n.created_at).toLocaleString()}
                      </p>
                    </div>
                    {!n.is_read && (
                      <button
                        type="button"
                        onClick={() => markRead(n.id)}
                        className="text-[10px] text-primary hover:underline"
                      >
                        mark read
                      </button>
                    )}
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
