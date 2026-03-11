import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.config import settings
from api.database import init_db
from api.routes.auth import router as auth_router
from api.routes.garments import router as garments_router
from api.routes.health import router as health_router
from api.routes.moodboards import router as moodboards_router
from api.routes.tryon import router as tryon_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    os.makedirs("static/garments", exist_ok=True)
    init_db()
    logger.info("Created storage directories: %s, %s",
                settings.UPLOAD_DIR, settings.RESULTS_DIR)
    yield


app = FastAPI(title="OnMe", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tryon_router)
app.include_router(moodboards_router)
app.include_router(garments_router)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/results", StaticFiles(directory=settings.RESULTS_DIR), name="results")
