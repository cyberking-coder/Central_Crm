/**
 * Minimal API client. Uses server-side INTERNAL_API_BASE_URL for SSR,
 * and NEXT_PUBLIC_API_BASE_URL for client components.
 * Credentials are always included so the backend session cookie is sent.
 */

export type HealthPayload = {
  status: "ok" | "degraded";
  service: string;
  version: string;
  database: { reachable: boolean; error: string | null };
  company_timezone: string;
  company_currency: string;
};

type Ok<T> = { ok: true; data: T };
type Err = { ok: false; error: string };

function baseUrl(): string {
  if (typeof window === "undefined") {
    return (
      process.env.INTERNAL_API_BASE_URL ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      "http://localhost:8000/api/v1"
    );
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";
}

export async function getApiHealth(): Promise<Ok<HealthPayload> | Err> {
  try {
    const res = await fetch(`${baseUrl()}/health/`, {
      cache: "no-store",
      credentials: "include",
    });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    const data = (await res.json()) as HealthPayload;
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  }
}
