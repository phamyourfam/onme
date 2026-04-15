"""
Virtual try-on upload and job status routes.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)

from api.auth import check_and_refresh_credits, get_current_user
from api.config import settings
from api.models import Job
from api.rate_limit import tryon_rate_limit
from api.repository import JobRepository
from api.schemas import JobResponse
from api.services.pipeline import execute_tryon_job

router = APIRouter(tags=["tryon"])

_repo = JobRepository()
logger = logging.getLogger("onme.api.tryon")

VALID_MODELS = {"catvton", "ootdiffusion"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/tryon", response_model=JobResponse)
@tryon_rate_limit
async def create_tryon(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    person: UploadFile = File(...),
    garment: UploadFile = File(...),
    model_name: str = Form(...),
    user_id: str = Depends(get_current_user),
) -> JobResponse:
    """Accept person and garment images, create a try-on job."""
    if model_name not in VALID_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_name '{model_name}'. Must be one of: {', '.join(sorted(VALID_MODELS))}",
        )

    for label, upload in [("person", person), ("garment", garment)]:
        if upload.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type for {label}: '{upload.content_type}'. Must be an image (JPEG, PNG, or WebP).",
            )

    await check_and_refresh_credits(user_id)

    job_id = uuid.uuid4().hex

    person_filename = f"{job_id}_person_{person.filename}"
    garment_filename = f"{job_id}_garment_{garment.filename}"

    person_path = settings.uploads_dir / person_filename
    garment_path = settings.uploads_dir / garment_filename

    with person_path.open("wb") as f:
        f.write(await person.read())
    with garment_path.open("wb") as f:
        f.write(await garment.read())

    now = datetime.now(timezone.utc).isoformat()

    job = Job(
        id=job_id,
        status="pending",
        model_name=model_name,
        person_image_path=str(person_path),
        garment_image_path=str(garment_path),
        created_at=now,
        user_id=user_id,
    )
    await _repo.create_job(job)
    background_tasks.add_task(execute_tryon_job, job.id)
    logger.info(
        "tryon_job_queued",
        extra={
            "user_id": user_id,
            "job_id": job.id,
            "model_name": job.model_name,
        },
    )

    return JobResponse(
        id=job.id,
        status=job.status,
        model_name=job.model_name,
        current_stage=job.current_stage,
        created_at=job.created_at,
        completed_at=job.completed_at,
        result_url=None,
        error_message=job.error_message,
        intermediates=None,
        timing=None,
    )


@router.get("/tryon/history", response_model=list[JobResponse])
async def get_tryon_history(
    user_id: str = Depends(get_current_user),
) -> list[JobResponse]:
    """Return all jobs for the authenticated user, newest first.

    Args:
        user_id: Injected by the auth dependency.

    Returns:
        A list of JobResponse objects.
    """
    jobs = await _repo.get_jobs_by_user(user_id)
    results = []
    for job in jobs:
        intermediates = (
            json.loads(job.intermediate_outputs)
            if job.intermediate_outputs
            else None
        )
        timing = {
            "preprocessing_ms": job.preprocessing_ms,
            "inference_ms": job.inference_ms,
            "postprocessing_ms": job.postprocessing_ms,
        }
        results.append(
            JobResponse(
                id=job.id,
                status=job.status,
                model_name=job.model_name,
                current_stage=job.current_stage,
                created_at=job.created_at,
                completed_at=job.completed_at,
                result_url=job.result_image_path,
                error_message=job.error_message,
                intermediates=intermediates,
                timing=timing,
            )
        )
    return results


@router.get("/tryon/{job_id}", response_model=JobResponse)
async def get_tryon(job_id: str) -> JobResponse:
    """Return the current state of a try-on job."""
    job = await _repo.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    intermediates = (
        json.loads(job.intermediate_outputs)
        if job.intermediate_outputs
        else None
    )
    timing = {
        "preprocessing_ms": job.preprocessing_ms,
        "inference_ms": job.inference_ms,
        "postprocessing_ms": job.postprocessing_ms,
    }

    return JobResponse(
        id=job.id,
        status=job.status,
        model_name=job.model_name,
        current_stage=job.current_stage,
        created_at=job.created_at,
        completed_at=job.completed_at,
        result_url=job.result_image_path,
        error_message=job.error_message,
        intermediates=intermediates,
        timing=timing,
    )
