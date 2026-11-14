import { apiGet } from "@/lib/api-server";
import type { LeadSource, Paginated } from "@/lib/types";
import { NewCampaignForm } from "./new-campaign-form";

export const dynamic = "force-dynamic";

export default async function NewCampaignPage() {
  const sources = await apiGet<Paginated<LeadSource>>("/lead-sources/");
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">New campaign</h1>
      </header>
      <NewCampaignForm sources={sources.ok ? sources.data.results : []} />
    </div>
  );
}
