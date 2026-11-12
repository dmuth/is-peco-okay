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

DATABASE_PATH="/app/${SQLITE_DATABASE_PATH}"

# Append a slash if it wasn't there.
S3_PREFIX="${PECO_BACKUPS_S3_PREFIX%/}/"

# Get the last object
S3_LISTING=$(aws s3 ls "$S3_PREFIX" --recursive)
LATEST_OBJECT=$(printf '%s\n' "$S3_LISTING" | sort | tail -n 1)
if [[ -z "$LATEST_OBJECT" ]]; then
    echo "No database backups found under ${S3_PREFIX}." >&2
    exit 1
fi

# Strip the path from the object then make a full S3 path to the object
LATEST_OBJECT="${LATEST_OBJECT##*/}"
S3_PATH="${S3_PREFIX}${LATEST_OBJECT}"

DATABASE_BACKUP=$(mktemp "${DATABASE_PATH}.backup.XXXXXX")
DATABASE_RESTORE=$(mktemp "${DATABASE_PATH}.restore.XXXXXX")

echo "# Restoring database from ${S3_PATH} to ${DATABASE_PATH}..."
aws s3 cp "${S3_PATH}" "$DATABASE_BACKUP"
gunzip -c "$DATABASE_BACKUP" > "$DATABASE_RESTORE"
mv "$DATABASE_RESTORE" "$DATABASE_PATH"

rm "$DATABASE_BACKUP"

/app/bin/cron.sh &

exec /app/bin/app-run.sh
