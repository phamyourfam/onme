"""
Virtual try-on upload and job status routes.
"""

import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.config import settings
from api.models import Job
from api.repository import JobRepository
from api.schemas import JobResponse

router = APIRouter(tags=["tryon"])

_repo = JobRepository()


@router.post("/tryon", response_model=JobResponse)
async def create_tryon(
    person: UploadFile = File(...),
    garment: UploadFile = File(...),
    model_name: str = Form(...),
) -> JobResponse:
    """Accept person and garment images, create a try-on job."""
    job_id = uuid.uuid4().hex

    person_filename = f"{job_id}_person_{person.filename}"
    garment_filename = f"{job_id}_garment_{garment.filename}"

    person_path = os.path.join(settings.UPLOAD_DIR, person_filename)
    garment_path = os.path.join(settings.UPLOAD_DIR, garment_filename)

    with open(person_path, "wb") as f:
        f.write(await person.read())
    with open(garment_path, "wb") as f:
        f.write(await garment.read())

    now = datetime.now(timezone.utc).isoformat()

    job = Job(
        id=job_id,
        status="pending",
        model_name=model_name,
        person_image_path=person_path,
        garment_image_path=garment_path,
        created_at=now,
    )
    _repo.create_job(job)

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


@router.get("/tryon/{job_id}", response_model=JobResponse)
async def get_tryon(job_id: str) -> JobResponse:
    """Return the current state of a try-on job."""
    job = _repo.get_job(job_id)
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
