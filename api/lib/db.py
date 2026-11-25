"""SQLite persistence for outage status and raw PECO archive records."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import sqlite3
from typing import Generator, Literal

import pytz


TableName = Literal["main", "archive"]
PECO_DB_MAIN_DAYS = int(os.environ.get("PECO_DB_MAIN_DAYS", "8"))
PECO_DB_ARCHIVE_DAYS = int(os.environ.get("PECO_DB_ARCHIVE_DAYS", "365"))
_MICROSECONDS_PER_SECOND = 1_000_000
_UTC_EPOCH = datetime(1970, 1, 1, tzinfo=pytz.utc)


@dataclass(frozen=True)
class SQLiteTable:
    """Identify a logical table and the SQLite database that stores it."""

    name: TableName
    database_path: Path


_SQL_TABLES = {
    "main": "main_records",
    "archive": "archive_records",
}


def _database_path() -> Path:
    """Resolve the configured SQLite database path or reject missing configuration."""

    database_path = os.environ.get("SQLITE_DATABASE_PATH")
    #
    # Fail early so callers cannot silently persist to an unintended location.
    #
    if not database_path:
        raise RuntimeError("SQLITE_DATABASE_PATH must be set in the environment")
    return Path(database_path).expanduser()


def _format_timestamp(value: datetime) -> str:
    """Format a datetime as a UTC collection timestamp for SQLite storage."""

    return value.astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")


def parse_timestamp_microseconds(value: str) -> int:
    """Convert an ISO timestamp to UTC microseconds since the Unix epoch.

    Naive timestamps are interpreted as UTC, while timezone-bearing timestamps
    are normalized to UTC before conversion.
    """

    #
    # datetime.fromisoformat accepts ISO timestamps with Z offsets only after
    # normalization to an explicit +00:00 timezone suffix.
    #
    value = value.replace("Z", "+00:00")
    if "." in value:
        date_part, remainder = value.split(".", 1)
        if "+" in remainder:
            fractional, timezone = remainder.split("+", 1)
            suffix = f"+{timezone}"
        elif "-" in remainder:
            fractional, timezone = remainder.split("-", 1)
            suffix = f"-{timezone}"
        else:
            fractional, suffix = remainder, ""
        #
        # Limit precision to microseconds because that is the storage unit used
        # for comparisons between PECO readings and the configured duration.
        #
        value = f"{date_part}.{fractional[:6]}{suffix}"

    parsed = datetime.fromisoformat(value)
    #
    # Treat timestamps without an offset as UTC because PECO readings do not
    # carry an offset in the naive-timestamp case.
    #
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=pytz.utc)
    delta = parsed.astimezone(pytz.utc) - _UTC_EPOCH
    return (
        (delta.days * 86400 + delta.seconds) * _MICROSECONDS_PER_SECOND
        + delta.microseconds
    )


def _initialize_database(database_path: Path) -> None:
    """Create the SQLite database, tables, and indexes when they do not exist."""

    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    try:
        #
        # WAL keeps collection writes from blocking reads and is persistent
        # across connections to this database.
        #
        connection.execute("PRAGMA journal_mode = WAL")

        #
        # Create the shared collection fields and add reading-time precision
        # only to the main table, where it supports duration-based lookups.
        #
        for table_name in _SQL_TABLES.values():
            reading_timestamp_column = (
                ", reading_timestamp INTEGER NOT NULL"
                if table_name == "main_records"
                else ""
            )
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    data TEXT NOT NULL
                    {reading_timestamp_column}
                )
                """
            )
            connection.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp "
                f"ON {table_name} (timestamp DESC)"
            )

        #
        # This index makes reading-time range queries and nearest-reading
        # searches efficient for the frequently queried main table.
        #
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_main_records_reading_timestamp "
            "ON main_records (reading_timestamp DESC)"
        )
        connection.commit()
    finally:
        connection.close()


def get_table(key: TableName) -> SQLiteTable:
    """Return a handle for the main or archive table, creating storage if needed."""

    #
    # Reject unknown logical names before resolving or initializing a database.
    #
    if key not in _SQL_TABLES:
        raise ValueError(f"Unknown key for SQLite table: {key}")

    database_path = _database_path()
    _initialize_database(database_path)
    return SQLiteTable(name=key, database_path=database_path)


@contextmanager
def _connection(table: SQLiteTable) -> Generator[sqlite3.Connection, None, None]:
    """Open a transaction that commits on success and rolls back on failure."""

    connection = sqlite3.connect(table.database_path, timeout=30)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def purge_expired_records() -> int:
    """Purge records according to the configured retention periods."""

    now = datetime.now(pytz.utc)

    #
    # Main records expire by PECO reading time, while archive rows expire by
    # collection time because the archive table has no reading-time column.
    #
    main_expiration = now - timedelta(days=PECO_DB_MAIN_DAYS)
    archive_expiration = now - timedelta(days=PECO_DB_ARCHIVE_DAYS)
    main_expiration_us = parse_timestamp_microseconds(main_expiration.isoformat())

    table = get_table("main")
    with _connection(table) as connection:
        main_cursor = connection.execute(
            "DELETE FROM main_records WHERE reading_timestamp <= ?",
            (main_expiration_us,),
        )
        archive_cursor = connection.execute(
            "DELETE FROM archive_records WHERE timestamp <= ?",
            (_format_timestamp(archive_expiration),),
        )
        return main_cursor.rowcount + archive_cursor.rowcount


def get_dates() -> dict[str, str]:
    """Return current UTC time at collection and reading-timestamp precision."""

    now = datetime.now(pytz.utc)
    return {
        "timestamp": _format_timestamp(now),
        "timestamp_us": str(parse_timestamp_microseconds(now.isoformat())),
    }


def _json_default(value: object) -> int | float:
    """Convert Decimal values or reject unsupported JSON value types."""

    #
    # Preserve fractional values as floats and integral Decimal values as ints
    # so serialized payloads retain a JSON-native numeric representation.
    #
    if isinstance(value, Decimal):
        if value.as_tuple().exponent:
            return float(value)
        return int(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def put_item(table: SQLiteTable, data: dict, timestamp: str) -> None:
    """Insert a record with its collection timestamp.

    Main-table records require PecoDateTime for reading-time queries; archive
    records accept the payload without that field.
    """

    payload = json.dumps(data, default=_json_default, separators=(",", ":"))

    with _connection(table) as connection:
        table_name = _SQL_TABLES[table.name]

        #
        # Main records index PECO's reading time separately from collection
        # time so retention and duration lookups follow the reading timeline.
        #
        if table.name == "main":
            reading_time = data.get("PecoDateTime")
            if not isinstance(reading_time, str):
                raise ValueError("Main status records require PecoDateTime")
            reading_timestamp = parse_timestamp_microseconds(reading_time)
            connection.execute(
                """
                INSERT INTO main_records (timestamp, data, reading_timestamp)
                VALUES (?, ?, ?)
                """,
                (timestamp, payload, reading_timestamp),
            )
        else:
            connection.execute(
                f"INSERT INTO {table_name} (timestamp, data) VALUES (?, ?)",
                (timestamp, payload),
            )


def _decode_row(row: tuple[str, str]) -> dict:
    """Decode a stored JSON payload and attach the collection timestamp."""

    data = json.loads(row[1])
    data["timestamp"] = row[0]
    return data


def get_latest_item(table: SQLiteTable) -> dict | None:
    """Return the latest row by collection timestamp."""

    with _connection(table) as connection:
        table_name = _SQL_TABLES[table.name]
        row = connection.execute(
            f"""
            SELECT timestamp, data FROM {table_name}
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
            """,
        ).fetchone()

    return _decode_row(row) if row is not None else None


def get_items_for_duration(
    table: SQLiteTable,
    end_timestamp_us: int,
    duration_seconds: int,
) -> list[dict]:
    """Return all main records within a PECO reading-time window.

    The end timestamp is inclusive, and duration_seconds must be positive.
    """

    #
    # Restrict this API to the main table because only it stores a PECO
    # reading timestamp that is independent of collection time.
    #
    if table.name != "main":
        raise ValueError("Duration lookup is only supported for the main table")

    #
    # Validate the duration before calculating the start boundary so a
    # non-positive window cannot produce an inverted or empty-range query.
    #
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")

    start_timestamp_us = end_timestamp_us - (
        duration_seconds * _MICROSECONDS_PER_SECOND
    )

    with _connection(table) as connection:
        rows = connection.execute(
            """
            SELECT timestamp, data FROM main_records
            WHERE reading_timestamp >= ? AND reading_timestamp <= ?
            ORDER BY reading_timestamp DESC, id DESC
            """,
            (start_timestamp_us, end_timestamp_us),
        ).fetchall()

    return [_decode_row(row) for row in rows]


def get_item_near_reading_time(
    table: SQLiteTable,
    target_timestamp_us: int,
    tolerance_seconds: int,
) -> dict | None:
    """Return the closest reading within the target's allowed time tolerance.

    The tolerance is inclusive. When readings are equally distant, the earlier
    reading wins; ties with the same reading timestamp use the latest inserted row.
    """

    #
    # Restrict nearest-reading lookup to the main table because archive records
    # do not store the PECO reading timestamp needed for this comparison.
    #
    if table.name != "main":
        raise ValueError("Reading-time lookup is only supported for the main table")

    #
    # A negative tolerance would create an invalid reversed search interval.
    #
    if tolerance_seconds < 0:
        raise ValueError("tolerance_seconds must not be negative")

    tolerance_us = tolerance_seconds * _MICROSECONDS_PER_SECOND
    with _connection(table) as connection:
        row = connection.execute(
            """
            SELECT timestamp, data FROM main_records
            WHERE reading_timestamp >= ? AND reading_timestamp <= ?
            ORDER BY ABS(reading_timestamp - ?), reading_timestamp, id DESC
            LIMIT 1
            """,
            (
                target_timestamp_us - tolerance_us,
                target_timestamp_us + tolerance_us,
                target_timestamp_us,
            ),
        ).fetchone()

    return _decode_row(row) if row is not None else None


def convert_decimals_to_ints(data: dict) -> dict:
    """Convert Decimal values in a dictionary to JSON-native float or int values.

    The input dictionary is mutated in place and is also returned for convenience.
    """

    #
    # Fractional decimals need floating-point representation; decimals whose
    # exponent indicates an integral value are converted to ints for consistency.
    #
    for key, value in data.items():
        if isinstance(value, Decimal):
            if value.as_tuple().exponent:
                data[key] = float(value)
            else:
                data[key] = int(value)

    return data
