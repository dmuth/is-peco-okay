FROM python:3.14-slim

RUN apt-get update \
    && apt-get install --no-install-recommends --yes awscli less \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --no-install-project

COPY api/ /app/api/
COPY bin/ /app/bin/
COPY hugo/public/ /app/hugo/public/

#RUN chmod +x /app/bin/cron.sh /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/bin/entrypoint.sh"]
