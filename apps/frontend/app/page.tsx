import { getApiHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const health = await getApiHealth();

  return (
    <main className="container py-16">
      <div className="mx-auto max-w-2xl space-y-8">
        <header className="space-y-2">
          <p className="text-sm uppercase tracking-widest text-muted">
            Central CRM
          </p>
          <h1 className="text-4xl font-semibold tracking-tight">
            Phase 1 foundation
          </h1>
          <p className="text-muted">
            Next.js and Django are wired up. Authentication and business modules
            arrive in Phase 2 onward.
          </p>
        </header>

        <section className="rounded-xl border border-border p-6">
          <h2 className="mb-4 text-lg font-medium">Backend health</h2>
          {health.ok ? (
            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
              <dt className="text-muted">Service</dt>
              <dd>{health.data.service}</dd>
              <dt className="text-muted">Version</dt>
              <dd>{health.data.version}</dd>
              <dt className="text-muted">Database</dt>
              <dd>{health.data.database.reachable ? "reachable" : "down"}</dd>
              <dt className="text-muted">Timezone</dt>
              <dd>{health.data.company_timezone}</dd>
              <dt className="text-muted">Currency</dt>
              <dd>{health.data.company_currency}</dd>
            </dl>
          ) : (
            <p className="text-sm text-red-500">
              Could not reach backend: {health.error}
            </p>
          )}
        </section>
      </div>
    </main>
  );
}
