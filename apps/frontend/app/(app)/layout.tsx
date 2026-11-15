import { redirect } from "next/navigation";

import { getMe } from "@/lib/auth-server";
import { Sidebar } from "@/components/sidebar";
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
    <div className="flex min-h-screen">
      <Sidebar permissions={me.permissions} />
      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-border bg-panel/80 backdrop-blur">
          <div className="flex items-center justify-end gap-3 px-6 py-3">
            {me.permissions.includes("notifications.read") ||
            me.permissions.includes("*") ? (
              <NotificationBell />
            ) : null}
            <div className="flex items-center gap-2 text-sm">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                {(me.full_name || me.email).slice(0, 1).toUpperCase()}
              </div>
              <div className="leading-tight">
                <p className="font-medium">{me.full_name || me.email}</p>
                <p className="text-xs text-muted">{me.role ?? "No role"}</p>
              </div>
            </div>
            <LogoutButton />
          </div>
        </header>
        <main className="flex-1 overflow-y-auto px-6 py-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
