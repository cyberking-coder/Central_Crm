/**
 * Server-side fetch wrapper that forwards cookies to the backend and
 * returns a typed result union. Use only in Server Components / Route
 * Handlers.
 */
import "server-only";
import { cookies } from "next/headers";

function base(): string {
  return (
    process.env.INTERNAL_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000/api/v1"
  );
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number; detail: string };

export async function apiGet<T>(path: string): Promise<ApiResult<T>> {
  const cookieHeader = cookies().toString();
  try {
    const res = await fetch(`${base()}${path}`, {
      cache: "no-store",
      headers: cookieHeader ? { cookie: cookieHeader } : {},
    });
    if (!res.ok) {
      return { ok: false, status: res.status, detail: await res.text() };
    }
    return { ok: true, data: (await res.json()) as T };
  } catch (e) {
    return { ok: false, status: 0, detail: e instanceof Error ? e.message : String(e) };
  }
}
