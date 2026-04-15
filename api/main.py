from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.config import settings
from api.database import close_database, init_models, ping_database
from api.logging_config import configure_logging
from api.rate_limit import limiter
from api.routes.auth import router as auth_router
from api.routes.garments import router as garments_router
from api.routes.health import router as health_router
from api.routes.moodboards import router as moodboards_router
from api.routes.tryon import router as tryon_router

configure_logging(environment=settings.environment)
logger = logging.getLogger("onme.api")

_LOCAL_CORS_HOSTS = {"localhost", "127.0.0.1", "::1"}


def build_cors_origins(origins: list[str]) -> list[str]:
    validated_origins: list[str] = []

    for origin in origins:
        if "*" in origin:
            raise RuntimeError(
                "ALLOWED_ORIGINS must not contain wildcard origins."
            )

        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise RuntimeError(
                f"Invalid CORS origin '{origin}'. Expected scheme://host[:port]."
            )
        if parsed.username or parsed.password:
            raise RuntimeError(
                f"Invalid CORS origin '{origin}'. Credentials are not allowed."
            )
        if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
            raise RuntimeError(
                f"Invalid CORS origin '{origin}'. Origins must not include a path, query, or fragment."
            )

        host = parsed.hostname.lower()
        is_localhost = host in _LOCAL_CORS_HOSTS
        is_cloudflare_pages = (
            parsed.scheme == "https" and host.endswith(".pages.dev")
        )

        if not (is_localhost or is_cloudflare_pages):
            raise RuntimeError(
                "ALLOWED_ORIGINS entries must be localhost or Cloudflare Pages origins."
            )
        if is_cloudflare_pages and parsed.port is not None:
            raise RuntimeError(
                "Cloudflare Pages origins must not specify an explicit port."
            )

        normalized_host = f"[{host}]" if ":" in host else host
        normalized_origin = f"{parsed.scheme}://{normalized_host}"
        if parsed.port is not None:
            normalized_origin = f"{normalized_origin}:{parsed.port}"

        if normalized_origin not in validated_origins:
            validated_origins.append(normalized_origin)

    return validated_origins


def ensure_asset_directories() -> None:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.results_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.started_at_monotonic = time.monotonic()
    ensure_asset_directories()
    await init_models()
    await ping_database()
    logger.info(
        "startup_checks_passed",
        extra={"asset_storage_path": str(settings.asset_storage_path)},
    )
    yield
    await close_database()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(tryon_router)
api_router.include_router(moodboards_router)
api_router.include_router(garments_router)
app.include_router(api_router)

app.mount(
    "/api/uploads",
    StaticFiles(directory=str(settings.uploads_dir), check_dir=False),
    name="uploads",
)
app.mount(
    "/api/results",
    StaticFiles(directory=str(settings.results_dir), check_dir=False),
    name="results",
)
