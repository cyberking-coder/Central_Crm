/**
 * Client-side fetch wrapper. Uses credentials:"include" and sends the
 * CSRF cookie as X-CSRFToken on mutating requests.
 */

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(^|; )${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]!) : null;
}

function base(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";
}

async function ensureCsrf(): Promise<string> {
  let token = readCookie("csrftoken");
  if (!token) {
    await fetch(`${base()}/auth/csrf/`, { credentials: "include" });
    token = readCookie("csrftoken");
  }
  return token ?? "";
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    const detail = data?.error?.detail ?? data?.detail ?? data;
    return typeof detail === "string" ? detail : JSON.stringify(detail);
  } catch {
    return `HTTP ${res.status}`;
  }
}

type Json = Record<string, unknown> | unknown[];

async function request<T>(
  method: "GET" | "POST" | "PATCH" | "DELETE",
  path: string,
  body?: Json | FormData,
): Promise<{ ok: true; data: T } | { ok: false; error: string; status: number }> {
  const csrf = method === "GET" ? "" : await ensureCsrf();
  const headers: HeadersInit = {};
  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  if (csrf) headers["X-CSRFToken"] = csrf;
  const res = await fetch(`${base()}${path}`, {
    method,
    credentials: "include",
    headers,
    body: payload,
  });
  if (!res.ok) {
    return { ok: false, status: res.status, error: await parseError(res) };
  }
  if (res.status === 204) return { ok: true, data: undefined as T };
  return { ok: true, data: (await res.json()) as T };
}

export const api = {
  get: <T>(p: string) => request<T>("GET", p),
  post: <T>(p: string, body?: Json | FormData) => request<T>("POST", p, body),
  patch: <T>(p: string, body: Json) => request<T>("PATCH", p, body),
  del: <T>(p: string) => request<T>("DELETE", p),
};
