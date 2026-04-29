import type { NextConfig } from "next";

// For static export on GCS, set at build time so /_next assets load from the bucket URL, not site root.
// Example: NEXT_PUBLIC_ASSET_PREFIX=https://my-project-alex-site.storage.googleapis.com
const assetPrefix = process.env.NEXT_PUBLIC_ASSET_PREFIX?.trim() || "";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: 'export',
  assetPrefix: assetPrefix || undefined,
  images: {
    unoptimized: true
  },
  // For bucket-hosted static sites, trailing slashes map cleanly to /route/index.html exports.
  trailingSlash: true,
};

export default nextConfig;
