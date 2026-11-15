import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Proxy /api/* to the Django backend, preserving the exact URL
 * (including the trailing slash that APPEND_SLASH requires).
 *
 * Why not next.config.rewrites()? That path strips trailing slashes
 * before proxying, which pingpongs with Django:
 *   browser  → /api/v1/auth/csrf/   (with slash)
 *   vercel   → /api/v1/auth/csrf    (strips)
 *   django   → 301 /api/v1/auth/csrf/  (demands slash)
 *   loop.
 */
export function middleware(request: NextRequest) {
  const backend = process.env.BACKEND_ORIGIN;
  if (!backend) return NextResponse.next();
  const { pathname, search } = request.nextUrl;
  const target = `${backend}${pathname}${search}`;
  return NextResponse.rewrite(target);
}

export const config = {
  matcher: ["/api/:path*"],
};
