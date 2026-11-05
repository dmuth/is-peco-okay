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
    uv run python -m api.cron
    uv run python -m api.purge
    sleep 60
done

