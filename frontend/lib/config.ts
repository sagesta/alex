// API base URL for the portfolio FastAPI app (backend/api): /api/user, /api/accounts, /api/jobs, etc.
// Cloud Run mode: set NEXT_PUBLIC_API_URL as a Cloud Run env var on the frontend service at deploy time.
// - Leave empty to use same-origin relative /api/... (works when LB proxies /api/* to backend/api Cloud Run).
// - Set to e.g. https://alex-api-….run.app to call backend/api directly (CORS must allow frontend origin).

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
    // Same-origin: works when LB routes /api/* to the portfolio API (no CORS needed).
    return "";
  }

  return "";
};

/** Call at request time so env is always fresh (important for Cloud Run runtime env). */
