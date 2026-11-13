#!/bin/bash
#
# Run our regularly recurring scripts
#

# Errors are fatal
set -e 

# Change to the parent directory
pushd $(dirname $0)/.. > /dev/null

# Load environment variables and make them exportable
if test "${UV_PROJECT_ENVIRONMENT}" != "/app/.venv"
then
    echo "# Local environment detected, loading env file"
    set -a
    source ./env
    set +a
fi

SLEEP=60
#SLEEP=5 # Debugging

INTERVAL_CRON=60
#INTERVAL_CRON=7 # Debugging
INTERVAL_PURGE=3600
#INTERVAL_PURGE=16 # Debugging
INTERVAL_BACKUP=300
#INTERVAL_BACKUP=30 # Debugging

# Prime these values so that cron and purge run on the first loop
LAST_CRON=$((SECONDS - INTERVAL_CRON))
LAST_PURGE=$((SECONDS - INTERVAL_PURGE))
# Backups are NOT run on the first loop by design.
LAST_BACKUP=${SECONDS}
if test "${PECO_BACKUP_IMMEDIATE}"
then
    echo "# PECO_BACKUP_IMMEDIATE is set, running backup immediately"
    LAST_BACKUP=$((SECONDS - INTERVAL_BACKUP))
fi

#
# Main loop for all of our tasks
#
while true
do

    AGO=$(($SECONDS - $LAST_CRON))
    if (( AGO >= INTERVAL_CRON )); then
        echo "# Last cron was ${AGO} seconds ago, running cron..."   
        LAST_CRON=$SECONDS
        uv run python -m api.cron 2>&1 || true
    fi

    AGO=$(($SECONDS - $LAST_PURGE))
    if (( AGO >= INTERVAL_PURGE )); then
        echo "# Last purge was ${AGO} seconds ago, running purge..."
        LAST_PURGE=$SECONDS
        uv run python -m api.purge 2>&1 || true
    else
        NEXT=$(($INTERVAL_PURGE - $AGO))
        echo "# Last purge was ${AGO} seconds ago, next in ${NEXT} secs, skipping purge..."
    fi

    AGO=$(($SECONDS - $LAST_BACKUP))
    if (( AGO >= INTERVAL_BACKUP )); then
        echo "# Last backup was ${AGO} seconds ago, running backup..."
        LAST_BACKUP=$SECONDS
        ./bin/backup-db.sh 2>&1 || true
    else
        NEXT=$(($INTERVAL_BACKUP - $AGO))
        echo "# Last backup was ${AGO} seconds ago, next in ${NEXT} secs, skipping backup..."
    fi

    echo "# Sleeping for ${SLEEP} seconds..."
    sleep ${SLEEP}


done
