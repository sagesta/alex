#!/usr/bin/env python3
"""
Deploy the portfolio FastAPI (backend/api) to Cloud Run — separate from alex-researcher.

Prereqs: Docker, gcloud, authenticated to GCP (e.g. GOOGLE_APPLICATION_CREDENTIALS or gcloud auth).

Required env (or set in repo-root .env next to this script — load manually):
  GCP_PROJECT_ID       — GCP project
  GCP_REGION           — e.g. europe-west4
  ARTIFACT_REGISTRY_URL — e.g. europe-west4-docker.pkg.dev/PROJECT_ID/alex-images (no trailing slash)
  CLERK_JWKS_URL       — Clerk JWKS URL (Dashboard → API / JWT)
  DATABASE_URL         — postgresql://… (copy from Secret Manager alex-database-url if needed)

Optional:
  CLOUD_RUN_API_SERVICE — default alex-api
  CLOUD_SQL_CONNECTION_NAME — project:region:instance for --add-cloudsql-instances (same as terraform output cloud_sql_connection_name)
  IMAGE_TAG            — default latest

Usage (from repo root, with uv):
  uv run scripts/deploy_portfolio_api_gcp.py

Or set vars inline (PowerShell):
  $env:GCP_PROJECT_ID="..."; uv run scripts/deploy_portfolio_api_gcp.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def need(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return v


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    env_file = repo_root / ".env"
    if env_file.is_file():
        # Minimal .env loader (KEY=VALUE lines, no export keyword)
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v

    project = need("GCP_PROJECT_ID")
    region = need("GCP_REGION")
    registry = need("ARTIFACT_REGISTRY_URL").rstrip("/")
    clerk = need("CLERK_JWKS_URL")
    database_url = need("DATABASE_URL")
    service = os.environ.get("CLOUD_RUN_API_SERVICE", "alex-api").strip() or "alex-api"
    tag = os.environ.get("IMAGE_TAG", "latest").strip() or "latest"
    cloudsql = os.environ.get("CLOUD_SQL_CONNECTION_NAME", "").strip()

    image = f"{registry}/api:{tag}"

    run(
        [
            "docker",
            "build",
            "--platform",
            "linux/amd64",
            "-f",
            "backend/api/Dockerfile",
            "-t",
            image,
            ".",
        ],
        cwd=repo_root,
    )
    run(["docker", "push", image], cwd=repo_root)

    # Avoid comma/special-char breakage in DATABASE_URL: use env-vars-file (YAML)
    env_yaml = Path(tempfile.gettempdir()) / "alex-api-cloudrun-env.yaml"
    payload = {"CLERK_JWKS_URL": clerk, "DATABASE_URL": database_url}
    lines = []
    for k, v in payload.items():
        lines.append(f"{k}: {json.dumps(v)}")
    env_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd = [
        "gcloud",
        "run",
        "deploy",
        service,
        "--image",
        image,
        "--region",
        region,
        "--project",
        project,
        "--platform",
        "managed",
        "--allow-unauthenticated",
        "--port",
        "8080",
        "--memory",
        "512Mi",
        "--cpu",
        "1",
        "--timeout",
        "120",
        "--env-vars-file",
        str(env_yaml),
        "--quiet",
    ]
    if cloudsql:
        cmd.insert(-1, f"--add-cloudsql-instances={cloudsql}")

    run(cmd, cwd=repo_root)

    out = subprocess.run(
        [
            "gcloud",
            "run",
            "services",
            "describe",
            service,
            "--region",
            region,
            "--project",
            project,
            "--format",
            "value(status.url)",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    url = out.stdout.strip()
    print()
    print("Deployed portfolio API:", url)
    print()
    print("Next steps:")
    print("  1. Set GitHub Variable or Secret NEXT_PUBLIC_API_URL to that URL.")
    print("  2. Rebuild the static frontend (Docker GCP workflow or npm run build + gsutil rsync).")
    print("  3. Open the site from index.html or your load balancer URL — not the raw bucket root.")


if __name__ == "__main__":
    main()
