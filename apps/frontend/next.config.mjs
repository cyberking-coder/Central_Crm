/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Keep trailing slashes so /api/v1/.../ isn't normalised to /api/v1/...
  // before middleware runs. Django's APPEND_SLASH insists on the slash.
  trailingSlash: true,
  // Don't redirect the browser when normalising — just rewrite internally
  // so our middleware can proxy whatever the client actually sent.
  skipTrailingSlashRedirect: true,
};

export default nextConfig;
