"""
Domain models as plain Python dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Job:
    """
    A single virtual try-on pipeline execution.

    Tracks status progression through pipeline stages:
    pending -> preprocessing -> inferring -> postprocessing -> complete

    The intermediate_outputs field stores a JSON string mapping
    stage names to image file paths, enabling the frontend to
    display thumbnails at each pipeline node during processing.

    Attributes:
        id: Hex UUID uniquely identifying this job.
        status: Current pipeline stage or terminal state.
        model_name: VTON model to use ('catvton' or 'ootdiffusion').
        person_image_path: Path to uploaded person photo on disk.
        garment_image_path: Path to uploaded garment photo on disk.
        result_image_path: Path to final output image, set on completion.
        intermediate_outputs: JSON string mapping stage names to file paths.
        error_message: Error details if status is 'failed'.
        current_stage: The stage currently being processed, for polling.
        created_at: ISO 8601 UTC timestamp of job creation.
        completed_at: ISO 8601 UTC timestamp of job completion.
        preprocessing_ms: Wall-clock time for preprocessing stage.
        inference_ms: Wall-clock time for model inference stage.
        postprocessing_ms: Wall-clock time for postprocessing stage.
    """

    id: str
    status: str
    model_name: str
    person_image_path: str
    garment_image_path: str
    result_image_path: str | None = None
    intermediate_outputs: str | None = None
    error_message: str | None = None
    current_stage: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: str | None = None
    preprocessing_ms: int | None = None
    inference_ms: int | None = None
    postprocessing_ms: int | None = None
