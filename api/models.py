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
    user_id: str | None = None


@dataclass
class User:
    """A registered user with credit-based access.

    Attributes:
        id: Hex UUID uniquely identifying this user.
        email: Unique email address used for login.
        hashed_password: Bcrypt hash of the user's password.
        credits_remaining: Number of try-on credits left today.
        last_credit_refresh: ISO 8601 UTC date of last credit reset.
        created_at: ISO 8601 UTC timestamp of account creation.
    """

    id: str
    email: str
    hashed_password: str
    credits_remaining: int = 10
    last_credit_refresh: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class Garment:
    """A catalog garment available for virtual try-on.

    Attributes:
        id: Hex UUID uniquely identifying this garment.
        image_path: Path to the garment image on disk.
        category: Garment category (tops, bottoms, dresses, outerwear).
        display_name: Human-readable name for the garment.
        source_credit: Optional attribution for the image source.
    """

    id: str
    image_path: str
    category: str
    display_name: str
    source_credit: str | None = None


@dataclass
class Moodboard:
    """A spatial canvas where users arrange garments, person photos,
    and try-on results.

    The canvas_state field holds a serialised JSON string of xyflow
    nodes and edges representing the spatial arrangement of garments,
    person photos, and try-on results on the board. This enables
    full save and restore of the board layout including positions,
    dimensions, and associated metadata for each element.

    Attributes:
        id: Hex UUID uniquely identifying this moodboard.
        user_id: ID of the user who owns this moodboard.
        title: Display title of the moodboard.
        canvas_state: Serialised xyflow nodes/edges JSON string.
        created_at: ISO 8601 UTC timestamp of moodboard creation.
        updated_at: ISO 8601 UTC timestamp of last modification.
    """

    id: str
    user_id: str
    title: str = "Untitled"
    canvas_state: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
