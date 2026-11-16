from unittest import IsolatedAsyncioTestCase

from starlette.requests import Request
from starlette.responses import PlainTextResponse

from api.main import redirect_apex_to_www


class ApexRedirectTests(IsolatedAsyncioTestCase):
    async def test_apex_redirects_to_www_preserving_path_and_query(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "scheme": "https",
                "path": "/about/",
                "query_string": b"source=test",
                "headers": [(b"host", b"ispecookay.com")],
            }
        )
        response = await redirect_apex_to_www(request, self.call_next)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["location"],
            "https://www.ispecookay.com/about/?source=test",
        )

    async def test_www_hostname_is_not_redirected(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "scheme": "https",
                "path": "/version",
                "query_string": b"",
                "headers": [(b"host", b"www.ispecookay.com")],
            }
        )
        response = await redirect_apex_to_www(request, self.call_next)

        self.assertEqual(response.status_code, 200)

    async def call_next(self, request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")
