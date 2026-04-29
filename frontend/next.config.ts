import type { NextConfig } from "next";

// Cloud Run server mode.
// `output: standalone` produces a self-contained node server in .next/standalone that can run with `node server.js`.
// NEXT_PUBLIC_* env vars are injected as Cloud Run environment variables at deploy time.
const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
