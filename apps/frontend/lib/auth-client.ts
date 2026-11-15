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

// Cross-site: the frontend can't read the backend's csrftoken cookie via
// document.cookie, so read it from the JSON body. The cookie is still sent
// by the browser on the subsequent POST thanks to credentials:include.
let _cachedCsrf: string | null = null;

async function fetchCsrf(): Promise<string> {
  if (_cachedCsrf) return _cachedCsrf;
  const fromCookie = readCookie("csrftoken");
  if (fromCookie) {
    _cachedCsrf = fromCookie;
    return fromCookie;
  }
  const res = await fetch(`${clientBase()}/auth/csrf/`, {
    credentials: "include",
  });
  try {
    const data = (await res.json()) as { csrfToken?: string };
    _cachedCsrf = data.csrfToken ?? readCookie("csrftoken") ?? "";
  } catch {
    _cachedCsrf = readCookie("csrftoken") ?? "";
  }
  return _cachedCsrf;
}

export async function ensureCsrf(): Promise<void> {
  await fetchCsrf();
}

export async function clientLogin(
  email: string,
  password: string,
): Promise<{ ok: true; me: Me } | { ok: false; error: string }> {
  const csrf = await fetchCsrf();
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
  const csrf = await fetchCsrf();
  await fetch(`${clientBase()}/auth/logout/`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRFToken": csrf },
  });
}
