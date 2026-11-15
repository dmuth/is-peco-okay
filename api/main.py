from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .peco import router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def redirect_apex_to_www(request: Request, call_next):
    if request.url.hostname == "ispecookay.com":
        url = request.url.replace(
            scheme="https",
            netloc="www.ispecookay.com",
        )
        return RedirectResponse(url=str(url), status_code=302)
    return await call_next(request)


app.include_router(router)


@app.get("/version", response_class=PlainTextResponse)
def get_version() -> str:
    with (Path(__file__).parent / "version").open(encoding="utf-8") as version_file:
        return version_file.readline().rstrip("\r\n")


app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent.parent / "hugo" / "public", html=True),
    name="site",
)
