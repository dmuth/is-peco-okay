#!/bin/bash

set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

"$SCRIPT_DIR/build-site.sh"
docker build --tag peco-outage-stats "$PROJECT_DIR"
