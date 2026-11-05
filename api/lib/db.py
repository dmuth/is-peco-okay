"""SQLite persistence for outage status and raw PECO archive records."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Generator, Literal

import pytz


TableName = Literal["main", "archive"]
DEFAULT_DATABASE_PATH = "peco-outages.sqlite3"


@dataclass(frozen=True)
class SQLiteTable:
    name: TableName
    database_path: Path


_SQL_TABLES = {
    "main": "main_records",
    "archive": "archive_records",
}

_QUERY_COLUMNS = {
    "main": {
        "Date": '"Date"',
        "DateTime": '"DateTime"',
        "Hour": '"Hour"',
    },
    "archive": {
        "DateTime": '"DateTime"',
    },
}


def _database_path() -> Path:
    return Path(os.environ.get("SQLITE_DATABASE_PATH", DEFAULT_DATABASE_PATH)).expanduser()


def _initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    try:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS main_records (
                "Date" TEXT NOT NULL,
                "DateTime" TEXT NOT NULL,
                "Hour" TEXT,
                ttl INTEGER,
                data TEXT NOT NULL,
                PRIMARY KEY ("Date", "DateTime")
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS archive_records (
                "DateTime" TEXT PRIMARY KEY NOT NULL,
                data TEXT NOT NULL
            )
            """
        )
        connection.execute(
            'CREATE INDEX IF NOT EXISTS idx_main_date_hour_datetime '
            'ON main_records ("Date", "Hour", "DateTime" DESC)'
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_main_ttl "
            "ON main_records (ttl) WHERE ttl IS NOT NULL"
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
            "DELETE FROM main_records WHERE ttl IS NOT NULL AND ttl <= ?",
            (int(time.time()),),
        )
        return cursor.rowcount


def get_dates() -> dict[str, str]:
    """Return the date partitions used by the collector and status queries."""
    now = datetime.now(pytz.utc)

    return {
        "date": now.strftime("%Y-%m-%d"),
        "datetime": now.strftime("%Y-%m-%dT%H:%M:%S %Z"),
        "hour": now.strftime("%Y%m%d%H"),
        "yesterday": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
        "hour_yesterday": (now - timedelta(days=1)).strftime("%Y%m%d%H"),
    }


def _json_default(value: object) -> int | float:
    if isinstance(value, Decimal):
        if value.as_tuple().exponent:
            return float(value)
        return int(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def put_item(table: SQLiteTable, data: dict) -> None:
    """Insert or replace a record identified by the table's primary key."""
    payload = json.dumps(data, default=_json_default, separators=(",", ":"))

    with _connection(table) as connection:
        if table.name == "main":
            connection.execute(
                """
                INSERT INTO main_records ("Date", "DateTime", "Hour", ttl, data)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT ("Date", "DateTime") DO UPDATE SET
                    "Hour" = excluded."Hour",
                    ttl = excluded.ttl,
                    data = excluded.data
                """,
                (
                    data["Date"],
                    data["DateTime"],
                    data.get("Hour"),
                    int(data["ttl"]) if data.get("ttl") is not None else None,
                    payload,
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO archive_records ("DateTime", data)
                VALUES (?, ?)
                ON CONFLICT ("DateTime") DO UPDATE SET data = excluded.data
                """,
                (data["DateTime"], payload),
            )


def get_items(
    table: SQLiteTable,
    key: str,
    value: str,
    limit: int = 100,
) -> list[dict]:
    """Return matching rows in descending DateTime order."""
    column = _QUERY_COLUMNS[table.name].get(key)
    if column is None:
        raise ValueError(f"Unsupported query key for {table.name} table: {key}")
    if limit < 0:
        raise ValueError("limit must not be negative")

    with _connection(table) as connection:
        table_name = _SQL_TABLES[table.name]
        if table.name == "main":
            rows = connection.execute(
                f"""
                SELECT data FROM {table_name}
                WHERE {column} = ? AND (ttl IS NULL OR ttl > ?)
                ORDER BY "DateTime" DESC
                LIMIT ?
                """,
                (value, int(time.time()), limit),
            ).fetchall()
        else:
            rows = connection.execute(
                f"""
                SELECT data FROM {table_name}
                WHERE {column} = ?
                ORDER BY "DateTime" DESC
                LIMIT ?
                """,
                (value, limit),
            ).fetchall()

    return [json.loads(row[0]) for row in rows]


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
    retval = get_items(table, "Date", dates["date"], limit=limit)

    if len(retval) < limit:
        remaining = limit - len(retval)
        retval += get_items(table, "Date", dates["yesterday"], limit=remaining)

    return retval


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
    date_yesterday: str,
    hour_yesterday: str,
) -> dict | list:
    if table.name != "main":
        raise ValueError("24-hour lookup is only supported for the main table")

    with _connection(table) as connection:
        row = connection.execute(
            """
            SELECT data FROM main_records
            WHERE "Date" = ? AND "Hour" = ? AND (ttl IS NULL OR ttl > ?)
            ORDER BY "DateTime" DESC
            LIMIT 1
            """,
            (date_yesterday, hour_yesterday, int(time.time())),
        ).fetchone()

    if row is None:
        return []

    item = json.loads(row[0])
    if "humanized" in item:
        return []
    return item
