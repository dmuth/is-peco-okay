import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from api import cron
from api.lib import db


class DatabaseSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "outages.sqlite3"
        self.environment = patch.dict(
            os.environ,
            {"SQLITE_DATABASE_PATH": str(self.database_path)},
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def test_new_tables_use_ids_and_datetime_columns(self) -> None:
        main_table = db.get_table("main")
        archive_table = db.get_table("archive")

        with sqlite3.connect(self.database_path) as connection:
            for table_name in ("main_records", "archive_records"):
                columns = connection.execute(
                    f"PRAGMA table_info({table_name})"
                ).fetchall()
                self.assertEqual(
                    [(column[1], column[2]) for column in columns],
                    [("id", "INTEGER"), ("timestamp", "DATETIME"), ("data", "TEXT")],
                )
                self.assertEqual(columns[0][5], 1)
                self.assertIn(
                    "AUTOINCREMENT",
                    connection.execute(
                        "SELECT sql FROM sqlite_master WHERE name = ?",
                        (table_name,),
                    ).fetchone()[0],
                )

        for table in (main_table, archive_table):
            db.put_item(table, {"value": 1}, "2026-11-04 12:00:00")
            db.put_item(table, {"value": 2}, "2026-11-04 12:01:00")

        with sqlite3.connect(self.database_path) as connection:
            for table_name in ("main_records", "archive_records"):
                self.assertEqual(
                    connection.execute(
                        f"SELECT id FROM {table_name} ORDER BY id"
                    ).fetchall(),
                    [(1,), (2,)],
                )

    def test_insert_and_recent_lookup_use_timestamp(self) -> None:
        table = db.get_table("main")
        db.put_item(table, {"customers": 12}, "2026-11-04 12:00:00")

        result = db.get_items_recent(
            table,
            {
                "recent_start": "2026-11-04 00:00:00",
                "timestamp": "2026-11-04 23:59:59",
            },
        )

        self.assertEqual(result, [{"customers": 12, "timestamp": "2026-11-04 12:00:00"}])

    def test_purge_removes_records_older_than_seven_days(self) -> None:
        table = db.get_table("main")
        old_timestamp = "2026-10-01 00:00:00"
        current_timestamp = db.get_dates()["timestamp"]
        db.put_item(table, {"customers": 10}, old_timestamp)
        db.put_item(table, {"customers": 11}, current_timestamp)

        self.assertEqual(db.purge_expired_records(), 1)

    def test_collector_writes_timestamp_columns_without_legacy_fields(self) -> None:
        stats = {
            "date": "2026-11-04T12:00:00Z",
            "total_customers": 100,
            "total_customers_outage": 2,
            "total_outages": 1,
        }
        with patch.object(
            cron.peco,
            "get_stats",
            return_value=(stats, "https://example.test/data.json"),
        ):
            cron.main()

        with sqlite3.connect(self.database_path) as connection:
            main_payload = json.loads(
                connection.execute("SELECT data FROM main_records").fetchone()[0]
            )
            archive_payload = json.loads(
                connection.execute("SELECT data FROM archive_records").fetchone()[0]
            )
            main_columns = {
                column[1]
                for column in connection.execute("PRAGMA table_info(main_records)")
            }
            archive_columns = {
                column[1]
                for column in connection.execute("PRAGMA table_info(archive_records)")
            }

        self.assertEqual(main_columns, {"id", "timestamp", "data"})
        self.assertEqual(archive_columns, {"id", "timestamp", "data"})
        self.assertNotIn("Date", main_payload)
        self.assertNotIn("DateTime", main_payload)
        self.assertNotIn("Hour", main_payload)
        self.assertNotIn("ttl", main_payload)
        self.assertNotIn("DateTime", archive_payload)


if __name__ == "__main__":
    unittest.main()
