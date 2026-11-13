import { redirect } from "next/navigation";

import { getMe } from "@/lib/auth-server";
import { Nav } from "@/components/nav";
import { LogoutButton } from "@/components/logout-button";
import { NotificationBell } from "@/components/notification-bell";

export const dynamic = "force-dynamic";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const me = await getMe();
  if (!me) redirect("/login?next=/dashboard");

  return (
    <div className="min-h-screen">
      <header className="border-b border-border">
        <div className="container flex items-center justify-between gap-6 py-3">
          <div className="flex items-center gap-6">
            <div>
              <p className="text-xs uppercase tracking-widest text-muted">
                Central CRM
              </p>
            </div>
            <Nav permissions={me.permissions} />
          </div>
          <div className="flex items-center gap-3">
            {me.permissions.includes("notifications.read") ||
            me.permissions.includes("*") ? (
              <NotificationBell />
            ) : null}
            <span className="text-sm text-muted">
              {me.full_name || me.email}{" "}
              <span className="opacity-60">· {me.role ?? "No role"}</span>
            </span>
            <LogoutButton />
          </div>
        </div>
      </header>
      <main className="container py-8">{children}</main>
    </div>
  );
}
