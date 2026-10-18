# Digest CDS backend — FastAPI on a uv workspace (Ports & Adapters).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# 1) Resolve/install third-party dependencies first (cached layer).
COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY data-collection/pyproject.toml data-collection/pyproject.toml
COPY ingestion-service/pyproject.toml ingestion-service/pyproject.toml
COPY supabase-integration/pyproject.toml supabase-integration/pyproject.toml
RUN uv sync --frozen --no-install-workspace --no-dev

# 2) Copy the workspace sources and install the members themselves.
COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

# Railway/other hosts inject $PORT; default to 8000 for local docker runs.
CMD ["sh", "-c", "uv run --no-dev uvicorn backend.interface.http.app:create_default_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
