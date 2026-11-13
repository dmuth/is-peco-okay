#!/bin/bash
# 
# Back up our database to S3
#

# Errors are fatal
set -e

# Change to the root directory of the app
pushd $(dirname $0)/.. > /dev/null

function now_ms() {
    python3 -c 'import time; print(time.monotonic_ns() // 1_000_000)'
}

# Load environment variables and make them exportable
if test "${UV_PROJECT_ENVIRONMENT}" != "/app/.venv"
then
    echo "# Local environment detected, loading env file"
    set -a
    source ./env
    set +a
fi

if [[ -z "${SQLITE_DATABASE_PATH:-}" || "${PECO_BACKUPS_S3_PREFIX:-}" != s3://* ]]; then
    echo "# Backup requires SQLITE_DATABASE_PATH and an S3 PECO_BACKUPS_S3_PREFIX." >&2

else
    BACKUP_FILENAME="db-$(date -u +%Y%m%dT%H%M%S).gz"
    BACKUP_PATH="./${BACKUP_FILENAME}"
    BACKUP_DESTINATION="${PECO_BACKUPS_S3_PREFIX%/}/${BACKUP_FILENAME}"

    echo "# Gzipping database..."
    START_MS=$(now_ms)
    if gzip -c "$SQLITE_DATABASE_PATH" > "$BACKUP_PATH"; then
        TOTAL_MS=$(( $(now_ms) - START_MS ))
        TOTAL_SEC=$(printf '%d.%03d' "$((TOTAL_MS / 1000))" "$((TOTAL_MS % 1000))")
        echo "# Gzipped database size: $(wc -c < "$BACKUP_PATH") bytes in ${TOTAL_SEC} sec"

        echo "# Uploading backup to ${BACKUP_DESTINATION}..."
        START_MS=$(now_ms)
        if aws s3 cp "$BACKUP_PATH" "$BACKUP_DESTINATION"; then
            TOTAL_MS=$(( $(now_ms) - START_MS ))
            TOTAL_SEC=$(printf '%d.%03d' "$((TOTAL_MS / 1000))" "$((TOTAL_MS % 1000))")
            echo "# Uploaded backup to ${BACKUP_DESTINATION} in ${TOTAL_SEC} sec"
            rm "$BACKUP_PATH"
        else
            echo "# Backup upload failed; local backup retained at ${BACKUP_PATH}." >&2
        fi
    else
        echo "# Backup compression failed." >&2
        rm -f "$BACKUP_PATH"
    fi
fi

echo "# OK: Backup complete"
