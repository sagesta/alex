# Build from repository root (see .github/workflows/docker-gcp.yml):
#   docker build -f backend/researcher/Dockerfile .
# researcher/pyproject.toml depends on ../database (alex-database); a context of only backend/researcher breaks uv sync.

FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app
# Resolve `from src.litellm_model_factory ...`: package lives under /app/src and/or /database/src
ENV PYTHONPATH=/app:/database

RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN npx -y playwright install --with-deps chromium

RUN pip install --no-cache-dir uv

COPY backend/database /database
COPY backend/researcher/pyproject.toml backend/researcher/uv.lock /app/

WORKDIR /app
RUN uv sync --frozen --no-install-project

COPY backend/researcher/*.py /app/

# Keep `src` as a package directory at /app/src (not flattened into /app)
COPY backend/database/src/ /app/src/

# Fail the image build if this import does not work on Cloud Run
RUN PYTHONPATH=/app:/database /app/.venv/bin/python -c "from src.litellm_model_factory import create_litellm_model; print('import_ok')"

EXPOSE 8080
ENV PORT=8080
# Use venv Python directly so PYTHONPATH is honored (avoid uv run masking env for the child)
CMD ["sh", "-c", "exec /app/.venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
