#!/bin/bash

# Change to parent directory
pushd "$(dirname "$0")/.." > /dev/null

# Load environment variables and make them exportable
if test "${UV_PROJECT_ENVIRONMENT}" != "/app/.venv"
then
    echo "# Local environment detected, loading env file"
    set -a
    source ./env
    set +a
fi

proxy_args=()
if test "${TRUST_PROXY:-0}" == "1"
then
    proxy_args+=(--proxy-headers)
    proxy_args+=("--forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-*}")
fi

if test "${UV_PROJECT_ENVIRONMENT}" == "/app/.venv"
then
    echo "# Docker environment detected, listening on all interfaces"
    uv run uvicorn api.main:app --host 0.0.0.0 "${proxy_args[@]}"

else 
    echo "# Local environment detected, listening on localhost only"
    uv run uvicorn api.main:app "${proxy_args[@]}"

fi
