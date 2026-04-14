from __future__ import annotations

import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.config import settings
from api.database import database_is_available

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    db_ok = await database_is_available()
    payload = {
        "status": "ok" if db_ok else "degraded",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(
            time.monotonic() - request.app.state.started_at_monotonic,
            3,
        ),
        "database": {
            "status": "ok" if db_ok else "unavailable",
        },
    }
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content=payload,
    )
