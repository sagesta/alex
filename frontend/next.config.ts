import type { NextConfig } from "next";

// For static export on GCS, set at build time so /_next assets load from the bucket URL, not site root.
// Example: NEXT_PUBLIC_ASSET_PREFIX=https://storage.googleapis.com/my-project-alex-site
const assetPrefix = process.env.NEXT_PUBLIC_ASSET_PREFIX?.trim() || "";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: 'export',
  assetPrefix: assetPrefix || undefined,
  images: {
    unoptimized: true
  },
  // Disable automatic trailing slash redirect for API routes
  trailingSlash: false,
};

export default nextConfig;
