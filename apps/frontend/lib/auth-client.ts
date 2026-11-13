/**
 * Client-only auth helpers. Must only be imported from "use client" files.
 */
import type { Me } from "./auth-server";

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(^|; )${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]!) : null;
}

function clientBase(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";
}

export async function ensureCsrf(): Promise<void> {
  if (readCookie("csrftoken")) return;
  await fetch(`${clientBase()}/auth/csrf/`, { credentials: "include" });
}

export async function clientLogin(
  email: string,
  password: string,
): Promise<{ ok: true; me: Me } | { ok: false; error: string }> {
  await ensureCsrf();
  const csrf = readCookie("csrftoken") ?? "";
  const res = await fetch(`${clientBase()}/auth/login/`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf,
    },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    return {
      ok: false,
      error:
        res.status === 400 ? "Invalid credentials" : `Login failed (${res.status})`,
    };
  }
  return { ok: true, me: (await res.json()) as Me };
}

export async function clientLogout(): Promise<void> {
  await ensureCsrf();
  const csrf = readCookie("csrftoken") ?? "";
  await fetch(`${clientBase()}/auth/logout/`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRFToken": csrf },
  });
}
