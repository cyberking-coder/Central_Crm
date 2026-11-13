import { apiGet } from "@/lib/api-server";
import type { Paginated, Task } from "@/lib/types";
import { TasksTable } from "./tasks-table";

export const dynamic = "force-dynamic";

type SearchParams = { [key: string]: string | string[] | undefined };

export default async function TasksPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const scope = String(searchParams.scope ?? "mine");
  const path =
    scope === "mine"
      ? "/tasks/mine/"
      : scope === "overdue"
        ? "/tasks/?status=pending&ordering=due_at"
        : "/tasks/";
  const result = await apiGet<Paginated<Task> | Task[]>(path);

  let items: Task[] = [];
  let count = 0;
  if (result.ok) {
    if (Array.isArray(result.data)) {
      items = result.data;
      count = result.data.length;
    } else {
      items = result.data.results;
      count = result.data.count;
    }
    if (scope === "overdue") {
      const now = Date.now();
      items = items.filter(
        (t) => t.due_at && new Date(t.due_at).getTime() < now,
      );
      count = items.length;
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Tasks</h1>
          <p className="text-sm text-muted">
            {result.ok ? `${count} total` : "—"}
          </p>
        </div>
      </header>

      <div className="flex gap-2 border-b border-border">
        <TabLink href="/tasks?scope=mine" label="My tasks" active={scope === "mine"} />
        <TabLink
          href="/tasks?scope=overdue"
          label="Overdue"
          active={scope === "overdue"}
        />
        <TabLink href="/tasks?scope=all" label="All" active={scope === "all"} />
      </div>

      {!result.ok ? (
        <p className="text-red-400">Failed to load: {result.detail}</p>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted">
          No tasks here.
        </div>
      ) : (
        <TasksTable tasks={items} />
      )}
    </div>
  );
}

function TabLink({
  href,
  label,
  active,
}: {
  href: string;
  label: string;
  active: boolean;
}) {
  return (
    <a
      href={href}
      className={`border-b-2 px-3 py-2 text-sm ${
        active
          ? "border-primary text-fg"
          : "border-transparent text-muted hover:text-fg"
      }`}
    >
      {label}
    </a>
  );
}
