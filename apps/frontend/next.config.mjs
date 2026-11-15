/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // API proxying is done by middleware.ts — rewrites() silently strips
  // trailing slashes which conflict with Django's APPEND_SLASH and cause
  // an endless redirect loop.
};

export default nextConfig;
