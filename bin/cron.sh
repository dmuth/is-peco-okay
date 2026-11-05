#!/bin/bash
#
# Run our regularly recurring scripts
#

# Errors are fatal
set -e 

# Change to the parent directory
pushd $(dirname $0)/.. > /dev/null

while true
do
    #
    # If something like a timeout happens, don't let it kill the main loop.
    #
    uv run python -m api.cron 2>&1 || true
    uv run python -m api.purge 2>&1 || true

    sleep 60

done

