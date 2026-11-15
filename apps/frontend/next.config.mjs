/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Django URLs end in / and APPEND_SLASH redirects naked paths back —
  // without this Vercel strips our trailing slashes and the browser
  // ping-pongs between Vercel and Django forever.
  trailingSlash: true,
  async rewrites() {
    const backend = process.env.BACKEND_ORIGIN;
    if (!backend) return [];
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
