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
DEFAULT_DATABASE_PATH = "db.sqlite"


@dataclass(frozen=True)
class SQLiteTable:
    name: TableName
    database_path: Path


_SQL_TABLES = {
    "main": "main_records",
    "archive": "archive_records",
}

_QUERY_COLUMNS = {
    "main": {"timestamp": '"timestamp"'},
    "archive": {"timestamp": '"timestamp"'},
}


def _database_path() -> Path:
    return Path(os.environ.get("SQLITE_DATABASE_PATH", DEFAULT_DATABASE_PATH)).expanduser()


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")


def _initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    try:
        connection.execute("PRAGMA journal_mode = WAL")
        for table_name in _SQL_TABLES.values():
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    data TEXT NOT NULL
                )
                """
            )
            connection.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp "
                f"ON {table_name} (timestamp DESC)"
            )
        connection.commit()
    finally:
        connection.close()


def get_table(key: TableName) -> SQLiteTable:
    """Return a handle for the main or archive table, creating storage if needed."""
    if key not in _SQL_TABLES:
        raise ValueError(f"Unknown key for SQLite table: {key}")

    database_path = _database_path()
    _initialize_database(database_path)
    return SQLiteTable(name=key, database_path=database_path)


@contextmanager
def _connection(table: SQLiteTable) -> Generator[sqlite3.Connection, None, None]:
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
    """Delete expired main records and return the number of rows removed."""
    table = get_table("main")
    with _connection(table) as connection:
        cursor = connection.execute(
            "DELETE FROM main_records WHERE timestamp <= ?",
            (_format_timestamp(datetime.now(pytz.utc) - timedelta(days=7)),),
        )
        return cursor.rowcount


def get_dates() -> dict[str, str]:
    """Return collection and query-window timestamps in UTC."""
    now = datetime.now(pytz.utc)
    recent_start = (now - timedelta(days=1)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    hour_24_ago = now - timedelta(days=1)
    hour_24_ago_start = hour_24_ago.replace(minute=0, second=0, microsecond=0)

    return {
        "timestamp": _format_timestamp(now),
        "recent_start": _format_timestamp(recent_start),
        "hour_24_start": _format_timestamp(hour_24_ago_start),
        "hour_24_end": _format_timestamp(hour_24_ago_start + timedelta(hours=1)),
    }


def _json_default(value: object) -> int | float:
    if isinstance(value, Decimal):
        if value.as_tuple().exponent:
            return float(value)
        return int(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def put_item(table: SQLiteTable, data: dict, timestamp: str) -> None:
    """Insert a record with its collection timestamp."""
    payload = json.dumps(data, default=_json_default, separators=(",", ":"))

    with _connection(table) as connection:
        table_name = _SQL_TABLES[table.name]
        connection.execute(
            f"INSERT INTO {table_name} (timestamp, data) VALUES (?, ?)",
            (timestamp, payload),
        )


def get_items(
    table: SQLiteTable,
    key: str,
    value: str,
    limit: int = 100,
) -> list[dict]:
    """Return matching rows in descending timestamp order."""
    column = _QUERY_COLUMNS[table.name].get(key)
    if column is None:
        raise ValueError(f"Unsupported query key for {table.name} table: {key}")
    if limit < 0:
        raise ValueError("limit must not be negative")

    with _connection(table) as connection:
        table_name = _SQL_TABLES[table.name]
        rows = connection.execute(
            f"""
            SELECT timestamp, data FROM {table_name}
            WHERE {column} = ?
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            (value, limit),
        ).fetchall()

    return [_decode_row(row) for row in rows]


def _decode_row(row: tuple[str, str]) -> dict:
    data = json.loads(row[1])
    data["timestamp"] = row[0]
    return data


def sort_humanized_dict(item):
    if item == "datetime":
        return (0, item)
    elif item == "customers":
        return (1, item)
    elif item == "customers_outages":
        return (2, item)
    elif item == "outages":
        return (3, item)
    elif item == "customers_active_percent":
        return (4, item)

    return (99, item)


def get_items_recent(
    table: SQLiteTable,
    dates: dict[str, str],
    limit: int = 1,
) -> list[dict]:
    if limit < 0:
        raise ValueError("limit must not be negative")

    with _connection(table) as connection:
        table_name = _SQL_TABLES[table.name]
        rows = connection.execute(
            f"""
            SELECT timestamp, data FROM {table_name}
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            (dates["recent_start"], dates["timestamp"], limit),
        ).fetchall()

    return [_decode_row(row) for row in rows]


def convert_decimals_to_ints(data: dict) -> dict:
    for key, value in data.items():
        if isinstance(value, Decimal):
            if value.as_tuple().exponent:
                data[key] = float(value)
            else:
                data[key] = int(value)

    return data


def get_item_24hours_ago(
    table: SQLiteTable,
    hour_24_start: str,
    hour_24_end: str,
) -> dict | list:
    if table.name != "main":
        raise ValueError("24-hour lookup is only supported for the main table")

    with _connection(table) as connection:
        row = connection.execute(
            """
            SELECT timestamp, data FROM main_records
            WHERE timestamp >= ? AND timestamp < ?
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
            """,
            (hour_24_start, hour_24_end),
        ).fetchone()

    if row is None:
        return []

    item = _decode_row(row)
    if "humanized" in item:
        return []
    return item
