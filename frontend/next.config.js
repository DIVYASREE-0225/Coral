/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http:///api/:path*" },
    ];
  },
};

module.exports = nextConfig;
