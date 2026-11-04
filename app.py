from pathlib import Path

from dotenv import load_dotenv

# Read settings such as the Gmail details from a private .env file, if there is one
load_dotenv()

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import IS_PRODUCTION
from routers import players, auth, execs, club_sessions, fees, payments, expenses, transfers, dashboard, audit_logs, opening_balances, exports, income

# The /docs pages list every API route, so they're only available on your Mac
app = FastAPI(
    title="KICA Club Management API",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Don't guess file types (stops some tricks with uploaded or odd files)
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Other websites may not show our pages inside a frame (stops "clickjacking")
    response.headers["X-Frame-Options"] = "DENY"
    # Don't tell other sites which of our pages a link was clicked on
    response.headers["Referrer-Policy"] = "same-origin"

    if IS_PRODUCTION:
        # Browsers should only ever use HTTPS for this site, for the next year
        response.headers["Strict-Transport-Security"] = "max-age=31536000"

    return response


# ---------- The backend: every route lives under /api, e.g. /api/players/ ----------

api = APIRouter(prefix="/api")

api.include_router(players.router)
api.include_router(auth.router)
api.include_router(execs.router)
api.include_router(club_sessions.router)
api.include_router(fees.router)
api.include_router(payments.router)
api.include_router(expenses.router)
api.include_router(transfers.router)
api.include_router(dashboard.router)
api.include_router(audit_logs.router)
api.include_router(opening_balances.router)
api.include_router(exports.router)
api.include_router(income.router)

app.include_router(api)

# ---------- The frontend: the built React app (made by `npm run build`) ----------

FRONTEND_DIST = (Path(__file__).parent / "frontend" / "dist").resolve()

if FRONTEND_DIST.exists():
    # The JavaScript and CSS files Vite builds. Their names change on every build,
    # so browsers can safely keep them.
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def serve_frontend(path: str):
        # A wrong /api address should be a real "not found", not the React page
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        # Files at the top of dist, e.g. the favicon
        file = (FRONTEND_DIST / path).resolve()
        if path and file.is_file() and FRONTEND_DIST in file.parents:
            return FileResponse(file)

        # Every other page (/players, /fees, /players/12 ...) is handled by React Router.
        # "no-cache": always check for a newer index.html, so a new deploy shows up straight away.
        return FileResponse(
            FRONTEND_DIST / "index.html",
            headers={"Cache-Control": "no-cache"},
        )