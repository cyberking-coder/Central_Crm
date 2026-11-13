"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

import { api } from "@/lib/api-client";
import type { Task } from "@/lib/types";

export function TasksTable({ tasks }: { tasks: Task[] }) {
  const router = useRouter();
  const [pending, start] = useTransition();

  function complete(id: string) {
    start(async () => {
      await api.post(`/tasks/${id}/complete/`);
      router.refresh();
    });
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
          <tr>
            <th className="px-4 py-3">Title</th>
            <th className="px-4 py-3">Assignee</th>
            <th className="px-4 py-3">Priority</th>
            <th className="px-4 py-3">Due</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.id} className="border-t border-border hover:bg-border/10">
              <td className="px-4 py-3 font-medium">{t.title}</td>
              <td className="px-4 py-3 text-muted">
                {t.assignee_name ?? "—"}
              </td>
              <td className="px-4 py-3 capitalize">{t.priority}</td>
              <td className={`px-4 py-3 ${t.is_overdue ? "text-red-400" : "text-muted"}`}>
                {t.due_at ? new Date(t.due_at).toLocaleString() : "—"}
              </td>
              <td className="px-4 py-3 capitalize">{t.status.replace("_", " ")}</td>
              <td className="px-4 py-3 text-right">
                {t.status !== "completed" && t.status !== "cancelled" && (
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => complete(t.id)}
                    className="rounded-md border border-border px-2 py-1 text-xs hover:bg-border/30"
                  >
                    Complete
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
