// API base URL for browser calls.
// Default to same-origin /api/... so the Next.js server can proxy requests to
// backend/api using its runtime BACKEND_URL env var. This avoids baking a stale
// API URL into the browser bundle and avoids cross-origin CORS failures.

function trimBase(url: string): string {
  return url.replace(/\/$/, "");
}

export const getApiUrl = (): string => {
  const fromEnv =
    typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
      ? String(process.env.NEXT_PUBLIC_API_URL).trim()
      : "";
  if (fromEnv) {
    return trimBase(fromEnv);
  }

  // Default to same-origin. In Cloud Run this is handled by pages/api/[...path].ts.
  return "";
};

/** Call at request time so local/dev env overrides are picked up consistently. */
