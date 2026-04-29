# Build from repository root (same as backend/researcher/Dockerfile):
#   docker build -f backend/api/Dockerfile .
# Portfolio API: /api/user, /api/accounts, … — not the researcher service.

FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app:/database

RUN pip install --no-cache-dir uv

COPY backend/database /database
COPY backend/api/pyproject.toml /app/

WORKDIR /app
RUN uv sync --no-install-project

COPY backend/api/*.py /app/
COPY backend/database/src/ /app/src/

RUN PYTHONPATH=/app:/database /app/.venv/bin/python -c "from src import Database; print('import_ok')"

EXPOSE 8080
ENV PORT=8080
CMD ["sh", "-c", "exec /app/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
