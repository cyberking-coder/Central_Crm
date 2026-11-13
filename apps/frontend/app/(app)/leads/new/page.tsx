import { apiGet } from "@/lib/api-server";
import type { LeadSource, Paginated } from "@/lib/types";
import { NewLeadForm } from "./new-lead-form";

export const dynamic = "force-dynamic";

export default async function NewLeadPage() {
  const sources = await apiGet<Paginated<LeadSource>>("/lead-sources/");
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">New lead</h1>
        <p className="text-sm text-muted">
          Required fields are marked. Duplicates on phone or email will be
          flagged.
        </p>
      </header>
      <NewLeadForm sources={sources.ok ? sources.data.results : []} />
    </div>
  );
}
