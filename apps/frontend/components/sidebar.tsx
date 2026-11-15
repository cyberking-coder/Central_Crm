"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavItem = {
  href: string;
  label: string;
  perm?: string;
  icon: React.ReactNode;
  section?: string;
};

const ICONS = {
  dashboard: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>
  ),
  leads: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-3-3.87"/><path d="M4 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
  ),
  customers: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="7" r="4"/><path d="M5.5 21a7 7 0 0 1 13 0"/></svg>
  ),
  tasks: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="m9 11 3 3L22 4"/></svg>
  ),
  webinars: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
  ),
  finance: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
  ),
  campaigns: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/></svg>
  ),
  reports: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="M7 15l4-4 4 4 5-6"/></svg>
  ),
  plug: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22v-5"/><path d="M9 7V2"/><path d="M15 7V2"/><path d="M6 13V8a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v5a5 5 0 0 1-5 5h-2a5 5 0 0 1-5-5z"/></svg>
  ),
  key: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/></svg>
  ),
};

const ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: ICONS.dashboard, section: "Overview" },
  { href: "/leads", label: "Leads", perm: "leads.read", icon: ICONS.leads, section: "Pipeline" },
  { href: "/customers", label: "Customers", perm: "customers.read", icon: ICONS.customers, section: "Pipeline" },
  { href: "/tasks", label: "Tasks", perm: "tasks.read", icon: ICONS.tasks, section: "Pipeline" },
  { href: "/webinars", label: "Webinars", perm: "webinars.read", icon: ICONS.webinars, section: "Programs" },
  { href: "/finance", label: "Finance", perm: "finance.read", icon: ICONS.finance, section: "Finance" },
  { href: "/marketing/campaigns", label: "Campaigns", perm: "marketing.read", icon: ICONS.campaigns, section: "Growth" },
  { href: "/reports", label: "Reports", perm: "reports.read", icon: ICONS.reports, section: "Growth" },
  { href: "/settings/integrations", label: "Integrations", perm: "integrations.read", icon: ICONS.plug, section: "Settings" },
  { href: "/settings/webhooks", label: "Webhooks", perm: "integrations.read", icon: ICONS.plug, section: "Settings" },
  { href: "/settings/api-tokens", label: "API tokens", icon: ICONS.key, section: "Settings" },
];

export function Sidebar({ permissions }: { permissions: string[] }) {
  const pathname = usePathname();
  const has = (p: string | undefined) =>
    !p || permissions.includes("*") || permissions.includes(p);
  const visible = ITEMS.filter((i) => has(i.perm));
  const sections = Array.from(new Set(visible.map((i) => i.section ?? "")));

  return (
    <aside className="hidden h-screen w-56 flex-col border-r border-border bg-panel md:flex">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-xs font-bold text-primary-fg">
          C
        </div>
        <span className="text-sm font-semibold tracking-tight">Central CRM</span>
      </div>
      <nav className="flex-1 overflow-y-auto px-2">
        {sections.map((section) => (
          <div key={section} className="mb-2">
            {section && (
              <p className="px-3 pb-1 pt-3 text-[10px] font-semibold uppercase tracking-wider text-muted/70">
                {section}
              </p>
            )}
            {visible
              .filter((i) => (i.section ?? "") === section)
              .map((i) => {
                const active =
                  pathname === i.href || pathname.startsWith(i.href + "/");
                return (
                  <Link
                    key={i.href}
                    href={i.href}
                    className={`flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition ${
                      active
                        ? "bg-primary/10 text-primary font-medium"
                        : "text-fg/80 hover:bg-border/40 hover:text-fg"
                    }`}
                  >
                    <span className={active ? "text-primary" : "text-muted"}>
                      {i.icon}
                    </span>
                    {i.label}
                  </Link>
                );
              })}
          </div>
        ))}
      </nav>
    </aside>
  );
}
