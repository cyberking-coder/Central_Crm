import Link from "next/link";

type NavItem = { href: string; label: string; perm?: string };

const ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/leads", label: "Leads", perm: "leads.read" },
  { href: "/customers", label: "Customers", perm: "customers.read" },
  { href: "/tasks", label: "Tasks", perm: "tasks.read" },
  { href: "/webinars", label: "Webinars", perm: "webinars.read" },
  { href: "/finance", label: "Finance", perm: "finance.read" },
];

export function Nav({ permissions }: { permissions: string[] }) {
  const has = (p: string | undefined) =>
    !p || permissions.includes("*") || permissions.includes(p);

  return (
    <nav className="flex gap-1">
      {ITEMS.filter((i) => has(i.perm)).map((i) => (
        <Link
          key={i.href}
          href={i.href}
          className="rounded-md px-3 py-1.5 text-sm text-muted hover:bg-border/40 hover:text-fg"
        >
          {i.label}
        </Link>
      ))}
    </nav>
  );
}
