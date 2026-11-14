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

export type Task = {
  id: string;
  title: string;
  description: string;
  assignee: string;
  assignee_name: string | null;
  due_at: string | null;
  priority: "low" | "medium" | "high";
  status: "pending" | "in_progress" | "completed" | "cancelled";
  related_kind: "none" | "lead" | "customer" | "webinar" | "department";
  related_id: string | null;
  is_overdue: boolean;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type SalesActivity = {
  id: string;
  lead: string | null;
  customer: string | null;
  performed_by: string | null;
  performed_by_name: string | null;
  kind: string;
  kind_label: string;
  occurred_at: string;
  outcome: string;
  discussion_summary: string;
  next_action: string;
  duration_minutes: number | null;
  integration_ref: string;
  created_at: string;
};

export type FollowUp = {
  id: string;
  lead: string | null;
  customer: string | null;
  owner: string;
  owner_name: string | null;
  due_at: string;
  status: "open" | "done" | "cancelled";
  summary: string;
  is_overdue: boolean;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type InvoiceItem = {
  id: string;
  description: string;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  amount: string;
};

export type Invoice = {
  id: string;
  number: string;
  customer: string;
  customer_name: string;
  issued_date: string;
  due_date: string | null;
  currency: string;
  subtotal: string;
  tax: string;
  discount: string;
  total: string;
  status: "draft" | "issued" | "partially_paid" | "paid" | "void";
  notes: string;
  items: InvoiceItem[];
  created_at: string;
  updated_at: string;
};

export type Payment = {
  id: string;
  customer: string;
  customer_name: string;
  invoice: string | null;
  invoice_number: string | null;
  amount: string;
  currency: string;
  payment_date: string;
  method: string;
  transaction_reference: string;
  status: string;
  source: string;
  notes: string;
  external_event_ref: string;
  created_at: string;
  updated_at: string;
};

export type Webinar = {
  id: string;
  title: string;
  description: string;
  start_at: string;
  end_at: string;
  platform: string;
  registration_url: string;
  registration_limit: number;
  host: string | null;
  host_name: string | null;
  manager: string | null;
  manager_name: string | null;
  status: "scheduled" | "live" | "completed" | "cancelled";
  created_at: string;
  updated_at: string;
};

export type WebinarRegistration = {
  id: string;
  webinar: string;
  lead: string | null;
  customer: string | null;
  full_name: string;
  phone: string;
  email: string;
  registration_source: string | null;
  source_name: string | null;
  status: "registered" | "cancelled";
  external_ref: string;
  attendance_status: string | null;
  created_at: string;
};

export type WebinarStats = {
  registrations_total: number;
  registrations_cancelled: number;
  registrations_eligible: number;
  attended: number;
  partial: number;
  absent: number;
  attendance_rate_pct: number;
};

export type Notification = {
  id: string;
  kind: string;
  title: string;
  body: string;
  related_kind: string;
  related_id: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
};

export const LEAD_STATUSES = [
  "new", "unassigned", "assigned", "contacted", "interested",
  "follow_up", "webinar_invited", "webinar_registered",
  "qualified", "converted", "lost", "invalid",
] as const;

export type LeadStatus = (typeof LEAD_STATUSES)[number];
