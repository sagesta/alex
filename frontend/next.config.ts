import type { NextConfig } from "next";

// Cloud Run server mode.
// `output: standalone` produces a self-contained node server in .next/standalone that can run with `node server.js`.
// NEXT_PUBLIC_* env vars used by browser code are resolved at build time.
const apiBase = (process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL)?.trim().replace(/\/$/, "");
const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  images: {
    unoptimized: true,
  },
  async rewrites() {
    if (!apiBase) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
