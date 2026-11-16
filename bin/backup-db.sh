#!/bin/bash
# 
# Back up our database to S3
#

# Errors are fatal
set -e

# Maximum number of backups to retain for the current UTC day.
BACKUPS_TO_KEEP_TODAY=10

DRY_RUN=false
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != "--dry-run" ) ]]; then
    echo "Usage: $0 [--dry-run]" >&2
    exit 2
fi
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Change to the root directory of the app
pushd $(dirname $0)/.. > /dev/null

function now_ms() {
    python3 -c 'import time; print(time.monotonic_ns() // 1_000_000)'
}

function report_kept_backup() {
    local BACKUP_URI="${PECO_BACKUPS_S3_PREFIX%/}/$1"

    if [[ "$DRY_RUN" == true ]]; then
        echo "# Dry run: would keep ${BACKUP_URI}"
    else
        echo "# Keeping backup ${BACKUP_URI}"
    fi
}

function prune_old_backups() {
    local S3_BACKUP_PREFIX="${PECO_BACKUPS_S3_PREFIX%/}/db-"
    local S3_LOCATION="${PECO_BACKUPS_S3_PREFIX#s3://}"
    local S3_KEY_PREFIX="${S3_LOCATION#*/}"
    local S3_LISTING BACKUP_FILES TODAY TODAY_BACKUP_COUNT TODAY_BACKUP_INDEX
    local TODAY_BACKUPS_TO_REMOVE PREVIOUS_BACKUP PREVIOUS_DAY BACKUP_FILENAME BACKUP_DAY

    [[ "$S3_LOCATION" == */* ]] || S3_KEY_PREFIX=""

    if ! [[ "$BACKUPS_TO_KEEP_TODAY" =~ ^[1-9][0-9]*$ ]]; then
        echo "# BACKUPS_TO_KEEP_TODAY must be a positive integer." >&2
        return 1
    fi

    if ! S3_LISTING=$(aws s3 ls "$S3_BACKUP_PREFIX" --recursive); then
        echo "# Could not list backups under ${S3_BACKUP_PREFIX}; pruning failed." >&2
        return 1
    fi

    BACKUP_FILES=$({
        printf '%s\n' "$S3_LISTING"
        printf '%s\n' "$1"
    } | awk -v key_prefix="$S3_KEY_PREFIX" '
        {
            filename = $4
            if (NF == 1) {
                filename = $1
            }
            if (key_prefix != "" && index(filename, key_prefix "/") == 1) {
                filename = substr(filename, length(key_prefix) + 2)
            } else if (index(filename, "/") != 0) {
                next
            }
            if (filename ~ /^db-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]T[0-9][0-9][0-9][0-9][0-9][0-9]\.gz$/) {
                print filename
            }
        }
    ' | sort -u)
    TODAY=$(date -u +%Y%m%d)
    TODAY_BACKUP_COUNT=$(printf '%s\n' "$BACKUP_FILES" | awk -v today="$TODAY" 'substr($0, 4, 8) == today { count++ } END { print count + 0 }')
    TODAY_BACKUPS_TO_REMOVE=$((TODAY_BACKUP_COUNT - BACKUPS_TO_KEEP_TODAY))
    TODAY_BACKUP_INDEX=0
    PREVIOUS_BACKUP=""
    PREVIOUS_DAY=""

    while IFS= read -r BACKUP_FILENAME; do
        [[ -z "$BACKUP_FILENAME" ]] && continue
        BACKUP_DAY="${BACKUP_FILENAME:3:8}"

        if [[ "$BACKUP_DAY" == "$TODAY" ]]; then
            if [[ -n "$PREVIOUS_BACKUP" ]]; then
                report_kept_backup "$PREVIOUS_BACKUP"
                PREVIOUS_BACKUP=""
                PREVIOUS_DAY=""
            fi
            TODAY_BACKUP_INDEX=$((TODAY_BACKUP_INDEX + 1))
            if (( TODAY_BACKUP_INDEX <= TODAY_BACKUPS_TO_REMOVE )); then
                if [[ "$DRY_RUN" == true ]]; then
                    echo "# Dry run: would remove ${PECO_BACKUPS_S3_PREFIX%/}/${BACKUP_FILENAME}"
                else
                    echo "# Removing older backup ${BACKUP_FILENAME}..."
                    aws s3 rm "${PECO_BACKUPS_S3_PREFIX%/}/${BACKUP_FILENAME}"
                fi
            else
                report_kept_backup "$BACKUP_FILENAME"
            fi
            continue
        fi

        if [[ -n "$PREVIOUS_BACKUP" ]]; then
            if [[ "$BACKUP_DAY" == "$PREVIOUS_DAY" && "$BACKUP_DAY" < "$TODAY" ]]; then
                if [[ "$DRY_RUN" == true ]]; then
                    echo "# Dry run: would remove ${PECO_BACKUPS_S3_PREFIX%/}/${PREVIOUS_BACKUP}"
                else
                    echo "# Removing older backup ${PREVIOUS_BACKUP}..."
                    aws s3 rm "${PECO_BACKUPS_S3_PREFIX%/}/${PREVIOUS_BACKUP}"
                fi
            else
                report_kept_backup "$PREVIOUS_BACKUP"
            fi
        fi

        PREVIOUS_BACKUP="$BACKUP_FILENAME"
        PREVIOUS_DAY="$BACKUP_DAY"
    done <<< "$BACKUP_FILES"

    if [[ -n "$PREVIOUS_BACKUP" ]]; then
        report_kept_backup "$PREVIOUS_BACKUP"
    fi
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

    if [[ "$DRY_RUN" == true ]]; then
        echo "# Dry run: would gzip ${SQLITE_DATABASE_PATH} to ${BACKUP_PATH}"
        echo "# Dry run: would upload ${BACKUP_PATH} to ${BACKUP_DESTINATION}"
        prune_old_backups "$BACKUP_FILENAME"
    else
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
                prune_old_backups "$BACKUP_FILENAME"
            else
                echo "# Backup upload failed; local backup retained at ${BACKUP_PATH}." >&2
            fi
        else
            echo "# Backup compression failed." >&2
            rm -f "$BACKUP_PATH"
        fi
    fi
fi

if [[ "$DRY_RUN" == true ]]; then
    echo "# OK: Dry run complete"
else
    echo "# OK: Backup complete"
fi
