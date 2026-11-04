FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY libs ./libs/
COPY services/docmanager ./services/docmanager/

ENV UV_HTTP_TIMEOUT=180
ENV UV_HTTP_RETRIES=5

RUN uv sync --no-dev --package docmanager

EXPOSE 3001
