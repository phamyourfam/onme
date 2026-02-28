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
