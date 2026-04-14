from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.config import settings
from api.database import close_database, init_models, ping_database
from api.routes.auth import router as auth_router
from api.routes.garments import router as garments_router
from api.routes.health import router as health_router
from api.routes.moodboards import router as moodboards_router
from api.routes.tryon import router as tryon_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("onme.api")


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
        "Startup checks passed; assets rooted at %s",
        settings.asset_storage_path,
    )
    yield
    await close_database()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
