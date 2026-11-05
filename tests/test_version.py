from pathlib import Path
import unittest

from fastapi.responses import PlainTextResponse

from api.main import app, get_version


class VersionEndpointTests(unittest.TestCase):
    def test_version_returns_first_line_as_plain_text(self) -> None:
        route = next(
            route for route in app.routes if getattr(route, "path", None) == "/version"
        )
        version_file = Path(__file__).resolve().parents[1] / "api" / "version"

        self.assertIn("GET", route.methods)
        self.assertIs(route.response_class, PlainTextResponse)
        with version_file.open(encoding="utf-8") as file:
            expected_version = file.readline().rstrip("\r\n")
        self.assertEqual(get_version(), expected_version)


if __name__ == "__main__":
    unittest.main()
