import json
import os
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "fake-data.py"


class FakeDataScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "db.sqlite"
        self.saved_path = Path(f"{self.database_path}-saved")
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute("CREATE TABLE original (value TEXT)")
            connection.execute("INSERT INTO original VALUES ('preserved')")
        self.environment = os.environ.copy()
        self.environment["SQLITE_DATABASE_PATH"] = str(self.database_path)
        self.addCleanup(self.temp_dir.cleanup)

    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            cwd=ROOT,
            env=self.environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_no_action_leaves_database_unchanged(self) -> None:
        result = self.run_script()

        self.assertIn("usage:", result.stdout)
        self.assertIn("-g, --generate", result.stdout)
        self.assertIn("-r, --restore", result.stdout)
        self.assertFalse(self.saved_path.exists())
        with closing(sqlite3.connect(self.database_path)) as connection:
            self.assertEqual(
                connection.execute("SELECT value FROM original").fetchone()[0],
                "preserved",
            )

    def test_generate_and_restore(self) -> None:
        result = self.run_script("-g")

        self.assertTrue(self.saved_path.exists())
        self.assertIn("2881 fake records", result.stdout)
        with closing(sqlite3.connect(self.database_path)) as connection:
            count, earliest, latest = connection.execute(
                """
                SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                FROM main_records
                """
            ).fetchone()
            self.assertEqual(count, 2881)
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM archive_records"
                ).fetchone()[0],
                0,
            )
            samples = [
                json.loads(row[0])
                for row in connection.execute("SELECT data FROM main_records")
            ]
        self.assertEqual(
            (
                datetime.fromisoformat(latest) - datetime.fromisoformat(earliest)
            ).total_seconds(),
            10 * 24 * 60 * 60,
        )
        self.assertTrue(all(10 <= sample["outages"] <= 100 for sample in samples))
        self.assertTrue(
            all(100 <= sample["customers_outages"] <= 25_000 for sample in samples)
        )
        self.assertGreater(len({sample["outages"] for sample in samples}), 1)
        self.assertGreater(
            len({sample["customers_outages"] for sample in samples}),
            1,
        )
        self.assertTrue(
            all(
                abs(current["outages"] - previous["outages"]) <= 10
                for previous, current in zip(samples, samples[1:])
            )
        )
        self.assertTrue(
            all(
                abs(current["customers_outages"] - previous["customers_outages"])
                <= 100
                for previous, current in zip(samples, samples[1:])
            )
        )

        self.run_script("-r")

        self.assertFalse(self.saved_path.exists())
        with closing(sqlite3.connect(self.database_path)) as connection:
            self.assertEqual(
                connection.execute("SELECT value FROM original").fetchone()[0],
                "preserved",
            )


if __name__ == "__main__":
    unittest.main()
