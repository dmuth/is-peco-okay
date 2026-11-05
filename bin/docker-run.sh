#!/bin/bash

set -e

# Change to the parent directory
pushd $(dirname "$0")/.. > /dev/null

exec docker run --rm --interactive --tty \
    --env-file env \
    -p 8000:8000 \
    peco-outage-stats "$@"
