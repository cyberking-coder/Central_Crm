import { redirect } from "next/navigation";

import { getMe } from "@/lib/auth-server";
import { LogoutButton } from "@/components/logout-button";

export const dynamic = "force-dynamic";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const me = await getMe();
  if (!me) {
    redirect("/login?next=/dashboard");
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-border">
        <div className="container flex items-center justify-between py-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-muted">
              Central CRM
            </p>
            <p className="text-sm">
              {me.full_name || me.email}{" "}
              <span className="text-muted">· {me.role ?? "No role"}</span>
            </p>
          </div>
          <LogoutButton />
        </div>
      </header>
      <main className="container py-8">{children}</main>
    </div>
  );
}
