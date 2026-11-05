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

if test "${UV_PROJECT_ENVIRONMENT}" == "/app/.venv"
then
    echo "# Docker environment detected, listening on all interfaces"
    uv run uvicorn api.main:app --host 0.0.0.0

else 
    echo "# Local environment detected, listening on localhost only"
    uv run uvicorn api.main:app

fi
