#!/usr/bin/env python3
"""Temporarily replace the outage database with generated sample data."""

import argparse
from contextlib import closing
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import random
import sqlite3
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _database_paths() -> tuple[Path, Path]:
    configured_path = Path(os.environ.get("SQLITE_DATABASE_PATH", "db.sqlite")).expanduser()
    database_path = configured_path if configured_path.is_absolute() else ROOT / configured_path
    database_path = database_path.resolve()
    os.environ["SQLITE_DATABASE_PATH"] = str(database_path)
    return database_path, Path(f"{database_path}-saved")


def _checkpoint_database(database_path: Path) -> None:
    if not database_path.exists():
        return

    with closing(sqlite3.connect(database_path, timeout=30)) as connection:
        result = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    if result is not None and result[0] != 0:
        raise RuntimeError(f"Could not checkpoint database: {database_path}")
    if Path(f"{database_path}-wal").exists():
        raise RuntimeError(
            f"Database still has an active WAL file; close its users first: "
            f"{database_path}"
        )


def _remove_database_files(database_path: Path) -> None:
    for path in (
        database_path,
        Path(f"{database_path}-wal"),
        Path(f"{database_path}-shm"),
    ):
        path.unlink(missing_ok=True)


def _create_fake_database(database_path: Path) -> int:
    from api.lib import db

    db.get_table("main")
    db.get_table("archive")

    sample_count = 10 * 24 * 12 + 1
    end_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    customers = 2_000_000
    outages = random.randint(10, 100)
    customers_outages = random.randint(100, 25_000)
    records = []
    for index in range(sample_count):
        reading_time = end_time - timedelta(minutes=5 * (sample_count - index - 1))
        if index:
            outages = min(100, max(10, outages + random.randint(-10, 10)))
            customers_outages = min(
                25_000,
                max(100, customers_outages + random.randint(-100, 100)),
            )
        data = {
            "PecoDateTime": reading_time.isoformat().replace("+00:00", "Z"),
            "customers": customers,
            "customers_outages": customers_outages,
            "outages": outages,
            "customers_active_percent": (
                f"{(100 - customers_outages / customers * 100):.3f}"
            ),
        }
        records.append(
            (
                reading_time.strftime("%Y-%m-%d %H:%M:%S"),
                json.dumps(data, separators=(",", ":")),
                db.parse_timestamp_microseconds(reading_time.isoformat()),
            )
        )

    with closing(sqlite3.connect(database_path, timeout=30)) as connection:
        with connection:
            connection.executemany(
                """
                INSERT INTO main_records (timestamp, data, reading_timestamp)
                VALUES (?, ?, ?)
                """,
                records,
            )
    return sample_count


def _generate(database_path: Path, saved_path: Path) -> None:
    if not database_path.is_file():
        raise FileNotFoundError(f"Database does not exist: {database_path}")
    if saved_path.exists():
        raise FileExistsError(f"Saved database already exists: {saved_path}")

    _checkpoint_database(database_path)
    database_path.rename(saved_path)
    try:
        count = _create_fake_database(database_path)
    except Exception:
        _remove_database_files(database_path)
        saved_path.rename(database_path)
        raise

    print(f"Generated {count} fake records in {database_path}.")
    print(f"Original database saved as {saved_path}.")


def _restore(database_path: Path, saved_path: Path) -> None:
    if not saved_path.is_file():
        raise FileNotFoundError(f"Saved database does not exist: {saved_path}")

    _checkpoint_database(database_path)
    _remove_database_files(database_path)
    saved_path.rename(database_path)
    print(f"Restored database from {saved_path}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "-g",
        "--generate",
        action="store_true",
        help="save the current database and replace it with 10 days of fake data",
    )
    actions.add_argument(
        "-r",
        "--restore",
        action="store_true",
        help="replace the current database with the saved database",
    )
    args = parser.parse_args()

    if not args.generate and not args.restore:
        parser.print_help()
        return

    database_path, saved_path = _database_paths()
    if args.generate:
        _generate(database_path, saved_path)
    else:
        _restore(database_path, saved_path)


if __name__ == "__main__":
    main()
