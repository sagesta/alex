# Build from repository root (see .github/workflows/docker-gcp.yml):
#   docker build -f backend/researcher/Dockerfile .
# researcher/pyproject.toml depends on ../database (alex-database); a context of only backend/researcher breaks uv sync and imports (Cloud Run then crashes on startup).

FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN npx -y playwright install --with-deps chromium

RUN pip install --no-cache-dir uv

# Monorepo: alex-database must live at ../database relative to researcher (see pyproject [tool.uv.sources])
COPY backend/database /database
COPY backend/researcher/pyproject.toml backend/researcher/uv.lock /app/

WORKDIR /app
RUN uv sync --frozen --no-install-project

COPY backend/researcher/*.py /app/

EXPOSE 8080
# Cloud Run sets PORT; default matches gcloud --port if unset locally
ENV PORT=8080
CMD ["sh", "-c", "exec uv run uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
