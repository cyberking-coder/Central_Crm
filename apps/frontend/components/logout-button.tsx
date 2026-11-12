"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

import { clientLogout } from "@/lib/auth";

export function LogoutButton() {
  const router = useRouter();
  const [pending, start] = useTransition();
  return (
    <button
      type="button"
      disabled={pending}
      onClick={() =>
        start(async () => {
          await clientLogout();
          router.replace("/login");
          router.refresh();
        })
      }
      className="rounded-md border border-border px-3 py-1.5 text-sm disabled:opacity-60"
    >
      {pending ? "Signing out…" : "Sign out"}
    </button>
  );
}
