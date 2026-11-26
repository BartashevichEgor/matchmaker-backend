import sys
import time
import traceback
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from swagger_ui_bundle import swagger_ui_path

from app.api import (
    auth,
    catalogs,
    favorites,
    health,
    notifications,
    onboarding,
    profiles,
    projects,
    recommendations,
    swipes,
)
from app.core.config import ROOT, get_settings
from app.core.request_limits import RequestBodyLimitMiddleware

settings = get_settings()
docs_enabled = settings.environment != "production"
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
LOG_DIR = ROOT / "log"
LOG_DIR.mkdir(exist_ok=True)
logger.add(
    LOG_DIR / "matchmaker_{time:YYYY-MM-DD}.txt",
    level="DEBUG",
    rotation="00:00",
    retention="14 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)
app = FastAPI(
    title="Matchmaker API",
    version="0.2.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json" if docs_enabled else None,
    description="Student project matching. Register → verify email → login → profile → projects → match.",
)
# swagger-ui 4.15, bundled locally for an offline demo, reads OpenAPI 3.0.x.
# FastAPI 0.142 always initialises this setting as 3.1.0, so override the
# generated-document version explicitly rather than relying on its constructor.
app.openapi_version = "3.0.3"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)
app.include_router(health.router)
for module in (
    auth,
    profiles,
    catalogs,
    projects,
    recommendations,
    favorites,
    onboarding,
    swipes,
    notifications,
):
    app.include_router(module.router, prefix="/api/v1")
if docs_enabled:
    app.mount("/swagger-assets", StaticFiles(directory=str(swagger_ui_path)), name="swagger-assets")


@app.get("/", include_in_schema=False)
def home():
    return {"service": "matchmaker-api", "docs": "/docs" if docs_enabled else None, "health": "/health"}


if docs_enabled:

    @app.get("/docs", include_in_schema=False)
    def docs():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Matchmaker API — Swagger",
            swagger_js_url="/swagger-assets/swagger-ui-bundle.js",
            swagger_css_url="/swagger-assets/swagger-ui.css",
            swagger_favicon_url="/swagger-assets/favicon-32x32.png",
        )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Never echo passwords, tokens or submitted personal data in validation errors.
    errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errors)})


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    if exc.status_code == 429:
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limited"},
            headers=exc.headers,
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


@app.middleware("http")
async def log_request(request: Request, call_next):
    request_id = uuid4().hex
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        frame = traceback.extract_tb(exc.__traceback__)[-1]
        logger.error(
            "Unhandled request failure type={} function={} line={} request={}",
            type(exc).__name__,
            frame.name,
            frame.lineno,
            request_id,
        )
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )
    route = request.scope.get("route")
    path = getattr(route, "path", "static-or-unmatched")
    log = logger.error if response.status_code >= 500 else logger.info
    log(
        "{} {} status={} duration_ms={:.1f} request={}",
        request.method,
        path,
        response.status_code,
        (time.perf_counter() - started) * 1000,
        request_id,
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


# Keep this outermost so oversized chunked bodies never reach the request logger or routes.
app.add_middleware(RequestBodyLimitMiddleware, max_bytes=settings.max_request_body_bytes)
