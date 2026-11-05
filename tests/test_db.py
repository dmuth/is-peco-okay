import json
import os
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import pytz
from fastapi.responses import PlainTextResponse

from api import cron, peco as api_peco, purge
from api.lib import db


class DatabaseConfigurationTests(unittest.TestCase):
    def test_database_path_requires_environment_variable(self) -> None:
        with patch.dict(os.environ):
            os.environ.pop("SQLITE_DATABASE_PATH", None)
            with self.assertRaisesRegex(
                RuntimeError, "SQLITE_DATABASE_PATH must be set"
            ):
                db.get_table("main")


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

        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            for table_name in ("main_records", "archive_records"):
                columns = connection.execute(
                    f"PRAGMA table_info({table_name})"
                ).fetchall()
                self.assertEqual(
                    [(column[1], column[2]) for column in columns],
                    (
                        [
                            ("id", "INTEGER"),
                            ("timestamp", "DATETIME"),
                            ("data", "TEXT"),
                            ("reading_timestamp", "INTEGER"),
                        ]
                        if table_name == "main_records"
                        else [
                            ("id", "INTEGER"),
                            ("timestamp", "DATETIME"),
                            ("data", "TEXT"),
                        ]
                    ),
                )
                self.assertEqual(columns[0][5], 1)
                if table_name == "main_records":
                    self.assertEqual(columns[3][3], 1)
                self.assertIn(
                    "AUTOINCREMENT",
                    connection.execute(
                        "SELECT sql FROM sqlite_master WHERE name = ?",
                        (table_name,),
                    ).fetchone()[0],
                )

        for table in (main_table, archive_table):
            for value, timestamp in (
                (1, "2026-11-04 12:00:00"),
                (2, "2026-11-04 12:01:00"),
            ):
                data: dict[str, int | str] = {"value": value}
                if table.name == "main":
                    data["PecoDateTime"] = timestamp.replace(" ", "T") + "Z"
                db.put_item(table, data, timestamp)

        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            for table_name in ("main_records", "archive_records"):
                self.assertEqual(
                    connection.execute(
                        f"SELECT id FROM {table_name} ORDER BY id"
                    ).fetchall(),
                    [(1,), (2,)],
                )

    def test_latest_item_uses_collection_timestamp(self) -> None:
        table = db.get_table("main")
        db.put_item(
            table,
            {"customers": 12, "PecoDateTime": "2026-11-04T12:00:00Z"},
            "2026-11-04 12:00:00",
        )
        db.put_item(
            table,
            {"customers": 13, "PecoDateTime": "2026-11-05T00:00:00Z"},
            "2026-11-05 00:00:00",
        )

        self.assertEqual(
            db.get_latest_item(table),
            {
                "customers": 13,
                "PecoDateTime": "2026-11-05T00:00:00Z",
                "timestamp": "2026-11-05 00:00:00",
            },
        )

    def test_main_records_require_a_peco_reading_timestamp(self) -> None:
        table = db.get_table("main")

        with self.assertRaisesRegex(ValueError, "require PecoDateTime"):
            db.put_item(table, {"customers": 12}, "2026-11-04 12:00:00")

    def test_duration_lookup_returns_all_rows_in_timestamp_window(self) -> None:
        table = db.get_table("main")
        for timestamp, customers in (
            ("2026-11-04T11:59:59Z", 1),
            ("2026-11-04T12:00:00Z", 2),
            ("2026-11-04T12:30:00Z", 3),
            ("2026-11-04T13:00:00Z", 4),
            ("2026-11-04T13:00:01Z", 5),
        ):
            db.put_item(
                table,
                {"customers": customers, "PecoDateTime": timestamp},
                "2026-11-04 14:00:00",
            )

        result = db.get_items_for_duration(
            table,
            db.parse_timestamp_microseconds("2026-11-04T13:00:00Z"),
            3600,
        )

        self.assertEqual(
            result,
            [
                {"customers": 4, "PecoDateTime": "2026-11-04T13:00:00Z", "timestamp": "2026-11-04 14:00:00"},
                {"customers": 3, "PecoDateTime": "2026-11-04T12:30:00Z", "timestamp": "2026-11-04 14:00:00"},
                {"customers": 2, "PecoDateTime": "2026-11-04T12:00:00Z", "timestamp": "2026-11-04 14:00:00"},
            ],
        )

    def test_duration_lookup_has_no_record_count_limit(self) -> None:
        table = db.get_table("main")
        end_timestamp = datetime(2026, 11, 8, 12, tzinfo=pytz.utc)
        end_timestamp_us = db.parse_timestamp_microseconds(end_timestamp.isoformat())
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.executemany(
                """
                INSERT INTO main_records (timestamp, data, reading_timestamp)
                VALUES (?, ?, ?)
                """,
                [
                    (
                        "2026-11-08 12:00:00",
                        json.dumps(
                            {
                                "PecoDateTime": (
                                    end_timestamp - timedelta(minutes=index)
                                ).isoformat(),
                                "customers_outages": index,
                            }
                        ),
                        end_timestamp_us - index * 60 * 1_000_000,
                    )
                    for index in range(250)
                ],
            )

        result = db.get_items_for_duration(table, end_timestamp_us, 7 * 86400)

        self.assertEqual(len(result), 250)

    def test_duration_lookup_rejects_nonpositive_window(self) -> None:
        table = db.get_table("main")

        with self.assertRaisesRegex(ValueError, "must be positive"):
            db.get_items_for_duration(table, 1_798_000_000_000_000, 0)

    def test_reading_time_parser_truncates_nanoseconds_to_microseconds(self) -> None:
        self.assertEqual(
            db.parse_timestamp_microseconds("2026-11-04T12:00:00.123456789Z"),
            db.parse_timestamp_microseconds("2026-11-04T12:00:00.123456Z"),
        )

    def test_near_reading_time_chooses_closest_within_tolerance(self) -> None:
        table = db.get_table("main")
        target = db.parse_timestamp_microseconds("2026-11-04T13:00:00Z")
        for seconds_offset, customers_outages in ((-500, 1), (250, 2), (700, 3)):
            timestamp = datetime.fromtimestamp(
                (target + seconds_offset * 1_000_000) / 1_000_000,
                tz=pytz.utc,
            ).isoformat()
            db.put_item(
                table,
                {
                    "PecoDateTime": timestamp,
                    "customers_outages": customers_outages,
                },
                "2026-11-04 13:00:00",
            )

        result = db.get_item_near_reading_time(table, target, 600)
        if result is None:
            self.fail("Expected a reading within the tolerance window")
        self.assertEqual(result["customers_outages"], 2)

    def test_near_reading_time_returns_none_outside_tolerance(self) -> None:
        table = db.get_table("main")
        target = db.parse_timestamp_microseconds("2026-11-04T13:00:00Z")
        timestamp = datetime.fromtimestamp(
            (target - 601 * 1_000_000) / 1_000_000,
            tz=pytz.utc,
        ).isoformat()
        db.put_item(
            table,
            {"PecoDateTime": timestamp, "customers_outages": 1},
            "2026-11-04 13:00:00",
        )

        self.assertIsNone(db.get_item_near_reading_time(table, target, 600))

    def test_recent_endpoint_returns_all_rows_in_requested_duration(self) -> None:
        table = db.get_table("main")
        for timestamp, customers_outages in (
            ("2026-11-04 11:59:59", 1),
            ("2026-11-04 12:00:00", 2),
            ("2026-11-04 12:30:00", 3),
            ("2026-11-04 13:00:00", 4),
            ("2026-11-04 13:00:01", 5),
        ):
            db.put_item(
                table,
                {
                    "PecoDateTime": timestamp.replace(" ", "T") + "Z",
                    "customers_outages": customers_outages,
                    "outages": customers_outages,
                },
                timestamp,
            )

        dates = {
            "timestamp": "2026-11-04 13:00:00",
            "timestamp_us": str(
                db.parse_timestamp_microseconds("2026-11-04T13:00:00Z")
            ),
        }
        with patch.object(api_peco.db, "get_dates", return_value=dates):
            result = api_peco.get_status_recent("3600")

        if not isinstance(result, dict):
            self.fail(f"Expected status data, got {result}")
        self.assertEqual(
            [row["timestamp"] for row in result["recent"]],
            [
                "2026-11-04 13:00:00",
                "2026-11-04 12:30:00",
                "2026-11-04 12:00:00",
            ],
        )
        with patch.object(api_peco.db, "get_dates", return_value=dates):
            short_window_result = api_peco.get_status_recent("1")
        if not isinstance(short_window_result, dict):
            self.fail(f"Expected status data, got {short_window_result}")
        self.assertEqual(len(short_window_result["recent"]), 1)
        self.assertEqual(short_window_result["trends"]["1hour"]["num"], 2)

    def test_recent_endpoint_rejects_legacy_record_count_parameter(self) -> None:
        result = api_peco.get_status_recent(num="6")

        if not isinstance(result, PlainTextResponse):
            self.fail(f"Expected an error response, got {result}")
        self.assertEqual(result.status_code, 422)

    def test_recent_duration_parser_enforces_one_to_seven_days(self) -> None:
        self.assertEqual(api_peco.parse_args_recent("604800"), 604800)
        for value in ("0", "604801", "invalid"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                api_peco.parse_args_recent(value)

    def test_purge_applies_eight_day_status_and_one_year_archive_retention(self) -> None:
        table = db.get_table("main")
        archive_table = db.get_table("archive")
        now = datetime.now(pytz.utc)
        old_collection_time = db._format_timestamp(now - timedelta(days=9))
        recent_collection_time = db._format_timestamp(now - timedelta(days=7))
        db.put_item(
            table,
            {
                "customers": 10,
                "PecoDateTime": (now - timedelta(days=9)).isoformat(),
            },
            old_collection_time,
        )
        db.put_item(
            table,
            {
                "customers": 11,
                "PecoDateTime": (now - timedelta(days=7)).isoformat(),
            },
            recent_collection_time,
        )
        archive_expired_time = db._format_timestamp(now - timedelta(days=366))
        db.put_item(archive_table, {"value": "expired"}, archive_expired_time)
        db.put_item(archive_table, {"value": "retained"}, recent_collection_time)

        self.assertEqual(db.purge_expired_records(), 2)
        latest_main = db.get_latest_item(table)
        if latest_main is None:
            self.fail("Expected a retained main record")
        self.assertEqual(
            latest_main["customers"],
            11,
        )
        latest_archive = db.get_latest_item(archive_table)
        if latest_archive is None:
            self.fail("Expected a retained archive record")
        self.assertEqual(
            latest_archive["value"],
            "retained",
        )

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

        with closing(sqlite3.connect(self.database_path)) as connection, connection:
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

        self.assertEqual(
            main_columns,
            {"id", "timestamp", "data", "reading_timestamp"},
        )
        self.assertEqual(archive_columns, {"id", "timestamp", "data"})
        self.assertNotIn("Date", main_payload)
        self.assertNotIn("DateTime", main_payload)
        self.assertNotIn("Hour", main_payload)
        self.assertNotIn("ttl", main_payload)
        self.assertNotIn("DateTime", archive_payload)

    def test_purge_logs_removed_record_count(self) -> None:
        with self.assertLogs("api.purge", level="INFO") as captured:
            removed = purge.main()

        self.assertEqual(removed, 0)
        self.assertIn("Removed 0 expired records.", captured.output[0])

    def test_collector_logs_when_latest_result_is_a_duplicate(self) -> None:
        table = db.get_table("main")
        existing_date = "2026-11-04T12:00:00Z"
        db.put_item(table, {"PecoDateTime": existing_date}, db.get_dates()["timestamp"])
        stats = {
            "date": existing_date,
            "total_customers": 100,
            "total_customers_outage": 2,
            "total_outages": 1,
        }

        with patch.object(cron.peco, "get_stats", return_value=(stats, "")):
            with self.assertLogs("api.cron", level="INFO") as captured:
                cron.main()

        self.assertIn(
            f"PecoDateTime of {existing_date} matches. This result is not new, stopping now.",
            captured.output[0],
        )


if __name__ == "__main__":
    unittest.main()
