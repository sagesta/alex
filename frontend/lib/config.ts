// API base URL for the FastAPI backend.
// - Set NEXT_PUBLIC_API_URL at build time when the static site is on GCS and the API is elsewhere (e.g. Cloud Run).
// - Without it, non-localhost production used to use "" (relative /api/...), which hits storage.googleapis.com, not your API.

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

/** Resolved at first import — ensure NEXT_PUBLIC_API_URL is set in CI for GCS-hosted static export. */
export const API_URL = getApiUrl();
