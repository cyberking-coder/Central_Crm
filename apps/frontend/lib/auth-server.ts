/**
 * Server-only auth helpers. Imports next/headers and must not be
 * imported from any "use client" module.
 */
import "server-only";
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
