"""
Pydantic response models for the OnMe API.
"""

from pydantic import BaseModel


class JobResponse(BaseModel):
    """Public representation of a virtual try-on job."""

    id: str
    status: str
    model_name: str
    current_stage: str | None = None
    created_at: str
    completed_at: str | None = None
    result_url: str | None = None
    error_message: str | None = None
    intermediates: dict[str, str] | None = None
    timing: dict[str, int | None] | None = None


class RegisterRequest(BaseModel):
    """JSON body for user registration."""

    email: str
    password: str


class RegisterResponse(BaseModel):
    """Response after successful registration."""

    id: str
    email: str
    token: str


class LoginResponse(BaseModel):
    """Response after successful login."""

    access_token: str
    token_type: str


class AuthMeResponse(BaseModel):
    """Authenticated user profile returned to the SPA."""

    id: str
    email: str
    credits_remaining: int


class GarmentResponse(BaseModel):
    """Public representation of a garment catalog item."""

    id: str
    image_url: str
    category: str
    display_name: str
    source_credit: str | None = None


class MoodboardSummary(BaseModel):
    """Lightweight moodboard listing without canvas_state."""

    id: str
    title: str
    updated_at: str


class MoodboardDetail(BaseModel):
    """Full moodboard including canvas_state."""

    id: str
    title: str
    canvas_state: str | None = None
    created_at: str
    updated_at: str


class MoodboardCanvasUpdate(BaseModel):
    """JSON body for canvas state updates."""

    canvas_state: str


class MoodboardTitleUpdate(BaseModel):
    """JSON body for title updates."""

    title: str


class CreditsResponse(BaseModel):
    """Response showing remaining credits."""

    credits_remaining: int
