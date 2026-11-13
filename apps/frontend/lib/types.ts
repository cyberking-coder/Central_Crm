export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type LeadSource = {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
};

export type Lead = {
  id: string;
  full_name: string;
  phone: string;
  email: string;
  source: string | null;
  source_name: string | null;
  campaign: string | null;
  campaign_name: string | null;
  interested_product: string;
  status: string;
  priority: "low" | "medium" | "high";
  assigned_to: string | null;
  assigned_to_name: string | null;
  last_contacted_at: string | null;
  next_followup_at: string | null;
  notes: string;
  converted_customer: string | null;
  converted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Customer = {
  id: string;
  full_name: string;
  phone: string;
  email: string;
  address: string;
  source: string | null;
  source_name: string | null;
  assigned_to: string | null;
  assigned_to_name: string | null;
  status: "active" | "inactive" | "lost";
  tags: string[];
  notes: string;
  created_at: string;
  updated_at: string;
};

export type TimelineEvent = {
  id: string;
  kind: string;
  summary: string;
  data: Record<string, unknown>;
  actor: string | null;
  actor_email: string | null;
  occurred_at: string;
};

export const LEAD_STATUSES = [
  "new", "unassigned", "assigned", "contacted", "interested",
  "follow_up", "webinar_invited", "webinar_registered",
  "qualified", "converted", "lost", "invalid",
] as const;

export type LeadStatus = (typeof LEAD_STATUSES)[number];
