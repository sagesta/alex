// API base URL for the portfolio FastAPI app (backend/api): /api/user, /api/accounts, /api/jobs, etc.
// - Set NEXT_PUBLIC_API_URL at build time when the static site is on GCS (e.g. your Cloud Run URL for **api**, not alex-researcher).
// - The researcher service only exposes /research and /health — it does not implement /api/user.
// - Without NEXT_PUBLIC_API_URL, production used "" (relative /api/...), which hits the GCS host, not your API.

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

  if (typeof window !== "undefined") {
    if (
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1"
    ) {
      return "http://localhost:8000";
    }
    // Same-origin API only when front + API are served from one host (e.g. CloudFront → API).
    return "";
  }

  // Build / SSR: no window; rely on NEXT_PUBLIC_API_URL above or fall through.
  return "";
};

/** Call at request time (not a module-level constant) so static export always uses the built-in NEXT_PUBLIC_API_URL. */
