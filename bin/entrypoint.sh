#!/bin/bash

set -e

if test "$#" -gt 0
then
    exec "$@"
fi

if [[ -z "${PECO_BACKUPS_S3_PREFIX:-}" ]]; then
    echo "PECO_BACKUPS_S3_PREFIX must be set to restore the SQLite database." >&2
    exit 1
fi

./bin/restore-db.sh

/app/bin/cron.sh &

exec /app/bin/app-run.sh
