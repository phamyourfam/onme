"""Moodboard CRUD routes with canvas state persistence."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from api.auth import get_current_user
from api.models import Moodboard
from api.repositories.moodboard_repo import (
    create_moodboard as repo_create,
    delete_moodboard as repo_delete,
    get_moodboard as repo_get,
    list_user_moodboards as repo_list,
    update_moodboard_canvas as repo_update_canvas,
    update_moodboard_title as repo_update_title,
)

router = APIRouter(prefix="/moodboards", tags=["moodboards"])


class _CreateBody(BaseModel):
    """Optional JSON body for moodboard creation."""

    title: str = "Untitled"


class _CanvasUpdateBody(BaseModel):
    """JSON body for canvas state updates."""

    canvas_state: str


class _TitleUpdateBody(BaseModel):
    """JSON body for title updates."""

    title: str


@router.post("/")
def create_moodboard(
    body: _CreateBody | None = None,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Create a new moodboard for the authenticated user.

    Args:
        body: Optional JSON body with a title field.
        user_id: Injected by the auth dependency.

    Returns:
        A dict with id, title, created_at, and updated_at.
    """
    now = datetime.now(timezone.utc).isoformat()
    title = body.title if body else "Untitled"
    moodboard = Moodboard(
        id=uuid.uuid4().hex,
        user_id=user_id,
        title=title,
        created_at=now,
        updated_at=now,
    )
    repo_create(moodboard)
    return {
        "id": moodboard.id,
        "title": moodboard.title,
        "created_at": moodboard.created_at,
        "updated_at": moodboard.updated_at,
    }


@router.get("/")
def list_moodboards(
    user_id: str = Depends(get_current_user),
) -> list[dict]:
    """List all moodboards for the authenticated user.

    Does NOT include canvas_state in the response to keep
    the list view lightweight.

    Args:
        user_id: Injected by the auth dependency.

    Returns:
        A list of dicts with id, title, and updated_at.
    """
    moodboards = repo_list(user_id)
    return [
        {
            "id": m.id,
            "title": m.title,
            "updated_at": m.updated_at,
        }
        for m in moodboards
    ]


@router.get("/{moodboard_id}")
def get_moodboard(
    moodboard_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Get a single moodboard with full canvas state.

    Args:
        moodboard_id: The ID of the moodboard to fetch.
        user_id: Injected by the auth dependency.

    Returns:
        Full moodboard data including canvas_state.

    Raises:
        HTTPException: 404 if not found, 403 if not owned.
    """
    mb = repo_get(moodboard_id)
    if mb is None:
        raise HTTPException(status_code=404, detail="Moodboard not found")
    if mb.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to access this moodboard",
        )
    return {
        "id": mb.id,
        "title": mb.title,
        "canvas_state": mb.canvas_state,
        "created_at": mb.created_at,
        "updated_at": mb.updated_at,
    }


@router.put("/{moodboard_id}/canvas")
def update_canvas(
    moodboard_id: str,
    body: _CanvasUpdateBody,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Update the canvas state of a moodboard.

    Args:
        moodboard_id: The ID of the moodboard to update.
        body: JSON body with canvas_state string.
        user_id: Injected by the auth dependency.

    Returns:
        A dict confirming the update with the new updated_at.

    Raises:
        HTTPException: 404 if not found, 403 if not owned.
    """
    mb = repo_get(moodboard_id)
    if mb is None:
        raise HTTPException(status_code=404, detail="Moodboard not found")
    if mb.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to update this moodboard",
        )
    now = datetime.now(timezone.utc).isoformat()
    repo_update_canvas(moodboard_id, body.canvas_state, now)
    return {"id": moodboard_id, "updated_at": now}


@router.put("/{moodboard_id}/title")
def update_title(
    moodboard_id: str,
    body: _TitleUpdateBody,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Update the title of a moodboard.

    Args:
        moodboard_id: The ID of the moodboard to update.
        body: JSON body with title string.
        user_id: Injected by the auth dependency.

    Returns:
        A dict confirming the update with the new updated_at.

    Raises:
        HTTPException: 404 if not found, 403 if not owned.
    """
    mb = repo_get(moodboard_id)
    if mb is None:
        raise HTTPException(status_code=404, detail="Moodboard not found")
    if mb.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to update this moodboard",
        )
    now = datetime.now(timezone.utc).isoformat()
    repo_update_title(moodboard_id, body.title, now)
    return {"id": moodboard_id, "title": body.title, "updated_at": now}


@router.delete("/{moodboard_id}", status_code=204)
def delete_moodboard(
    moodboard_id: str,
    user_id: str = Depends(get_current_user),
) -> Response:
    """Delete a moodboard if owned by the authenticated user.

    Args:
        moodboard_id: The ID of the moodboard to delete.
        user_id: Injected by the auth dependency.

    Returns:
        204 No Content on success.

    Raises:
        HTTPException: 404 if not found or not owned.
    """
    deleted = repo_delete(moodboard_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Moodboard not found"
        )
    return Response(status_code=204)
