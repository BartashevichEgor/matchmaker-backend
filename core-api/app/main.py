import sys
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from swagger_ui_bundle import swagger_ui_path

from app.api import auth, catalogs, health, profiles, projects, recommendations, swipes
from app.core.config import ROOT, get_settings

settings = get_settings()
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
app = FastAPI(
    title="Matchmaker API",
    version="0.2.0",
    docs_url=None,
    redoc_url=None,
    description="Student project matching. Register → verify email → login → profile → projects → match.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(health.router)
for module in (auth, profiles, catalogs, projects, recommendations, swipes):
    app.include_router(module.router, prefix="/api/v1")
app.mount("/swagger-assets", StaticFiles(directory=str(swagger_ui_path)), name="swagger-assets")
app.mount("/assets", StaticFiles(directory=str(ROOT / "app" / "static")), name="assets")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "app" / "static" / "index.html")


@app.get("/docs", include_in_schema=False)
def docs():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Matchmaker API — Swagger",
        swagger_js_url="/swagger-assets/swagger-ui-bundle.js",
        swagger_css_url="/swagger-assets/swagger-ui.css",
        swagger_favicon_url="/assets/favicon.svg",
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Never echo passwords, tokens or submitted personal data in validation errors.
    errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errors)})


@app.middleware("http")
async def log_request(request: Request, call_next):
    request_id = uuid4().hex
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error("request={} failure={}", request_id, type(exc).__name__)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error", "request_id": request_id}
        )
    route = request.scope.get("route")
    path = getattr(route, "path", "static-or-unmatched")
    logger.info(
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
