import { getMe } from "@/lib/auth-server";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const me = (await getMe())!; // layout guarantees auth

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-muted">
          Business KPIs land in Phase 5. For now, verify your access below.
        </p>
      </header>

      <section className="rounded-xl border border-border p-6">
        <h2 className="mb-4 text-lg font-medium">Your access</h2>
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
          <dt className="text-muted">Email</dt>
          <dd>{me.email}</dd>
          <dt className="text-muted">Role</dt>
          <dd>{me.role ?? "—"}</dd>
          <dt className="text-muted">Permissions</dt>
          <dd className="font-mono text-xs">
            {me.permissions.length ? me.permissions.join(", ") : "—"}
          </dd>
        </dl>
      </section>
    </div>
  );
}
