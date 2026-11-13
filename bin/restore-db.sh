#!/bin/bash
# 
# Restore our database from S3
#

# Errors are fatal
set -e

# Change to the root directory of the app
pushd $(dirname $0)/.. > /dev/null

# Load environment variables and make them exportable
if test "${UV_PROJECT_ENVIRONMENT}" != "/app/.venv"
then
    echo "# Local environment detected, loading env file"
    set -a
    source ./env
    set +a
fi

function now_ms() {
    python3 -c 'import time; print(time.monotonic_ns() // 1_000_000)'
}
# Append a slash if it wasn't there.
S3_PREFIX="${PECO_BACKUPS_S3_PREFIX%/}/"

# Get the last object
echo "# Getting the latest database backup from ${S3_PREFIX}..."
S3_LISTING=$(aws s3 ls "$S3_PREFIX" --recursive)
LATEST_OBJECT=$(printf '%s\n' "$S3_LISTING" | sort | tail -n 1)
if [[ -z "$LATEST_OBJECT" ]]; then
    echo "No database backups found under ${S3_PREFIX}." >&2
    exit 1
fi

# Strip the path from the object then make a full S3 path to the object
LATEST_OBJECT="${LATEST_OBJECT##*/}"
S3_PATH="${S3_PREFIX}${LATEST_OBJECT}"

DATABASE_BACKUP=$(mktemp "${SQLITE_DATABASE_PATH}.backup.XXXXXX")
DATABASE_RESTORE=$(mktemp "${SQLITE_DATABASE_PATH}.restore.XXXXXX")

echo "# Restoring database from ${S3_PATH} to ${SQLITE_DATABASE_PATH}..."
START_MS=$(now_ms)
aws s3 cp "${S3_PATH}" "$DATABASE_BACKUP"
TOTAL_MS=$(( $(now_ms) - START_MS ))
TOTAL_SEC=$(printf '%d.%03d' "$((TOTAL_MS / 1000))" "$((TOTAL_MS % 1000))")
echo "# Downloaded ${DATABASE_BACKUP} in ${TOTAL_SEC} sec"

START_MS=$(now_ms)
gunzip -c "$DATABASE_BACKUP" > "$DATABASE_RESTORE"
TOTAL_MS=$(( $(now_ms) - START_MS ))
TOTAL_SEC=$(printf '%d.%03d' "$((TOTAL_MS / 1000))" "$((TOTAL_MS % 1000))")
DATABASE_RESTORE_BYTES=$(wc -c < "$DATABASE_RESTORE")
echo "# Restored database size: ${DATABASE_RESTORE_BYTES} bytes in ${TOTAL_SEC} sec"

mv "$DATABASE_RESTORE" "$SQLITE_DATABASE_PATH"

rm "$DATABASE_BACKUP"

echo "# OK: Database restored from ${S3_PATH}"
