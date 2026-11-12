/**
 * Auth helpers.
 *
 * Server-side: forwards the session cookie from the incoming request to the
 * internal backend so SSR `me` calls work.
 * Client-side: uses credentials: "include" and sends the CSRF header.
 */
import { cookies } from "next/headers";

export type Me = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  role: string | null;
  permissions: string[];
};

function serverBase(): string {
  return (
    process.env.INTERNAL_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000/api/v1"
  );
}

export async function getMe(): Promise<Me | null> {
  const cookieHeader = cookies().toString();
  try {
    const res = await fetch(`${serverBase()}/auth/me/`, {
      cache: "no-store",
      headers: cookieHeader ? { cookie: cookieHeader } : {},
    });
    if (!res.ok) return null;
    return (await res.json()) as Me;
  } catch {
    return null;
  }
}

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
