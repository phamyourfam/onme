"""Pipeline orchestrator that runs the full virtual try-on job as a background task."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from api.config import settings
from api.models import Job
from api.repository import JobRepository
from api.services.inference import run_and_save_sync
from api.services.postprocessing import run_postprocessing
from api.services.preprocessing import run_preprocessing

_repo = JobRepository()


async def execute_tryon_job(job_id: str) -> None:
    """Execute the full try-on pipeline for a given job.

    This function is designed to run inside a ``BackgroundTasks`` context.
    It drives the job through three stages — preprocessing, inference,
    and postprocessing — updating the database record at every transition
    so that the frontend can poll for progress.

    Args:
        job_id: The hex UUID of the job to process.
    """
    job = await _repo.get_job(job_id)
    if job is None:
        return

    intermediates: dict[str, str] = {}
    timing: dict[str, int] = {}

    try:
        # ── Stage 1: Preprocessing ──────────────────────────────────
        await _repo.update_job(
            job_id, status="preprocessing", current_stage="preprocessing"
        )

        t0 = time.monotonic()
        result = run_preprocessing(job.person_image_path, job.garment_image_path)
        timing["preprocessing_ms"] = int((time.monotonic() - t0) * 1000)

        intermediates["person_original"] = job.person_image_path
        intermediates["garment_original"] = job.garment_image_path
        intermediates["person_clahe"] = result["person_processed"]
        intermediates["garment_resized"] = result["garment_processed"]

        await _repo.update_job(
            job_id,
            intermediate_outputs=json.dumps(intermediates),
        )

        # ── Stage 2: Inference ──────────────────────────────────────
        await _repo.update_job(job_id, status="inferring", current_stage="inferring")

        t0 = time.monotonic()
        raw_output_path = str(settings.results_dir / f"{job_id}_raw.jpg")
        run_and_save_sync(
            model_name=job.model_name,
            person_image_path=result["person_processed"],
            garment_image_path=result["garment_processed"],
            output_path=raw_output_path,
        )
        timing["inference_ms"] = int((time.monotonic() - t0) * 1000)

        intermediates["inference_raw"] = raw_output_path
        await _repo.update_job(
            job_id,
            intermediate_outputs=json.dumps(intermediates),
        )

        # ── Stage 3: Postprocessing ────────────────────────────────
        await _repo.update_job(
            job_id,
            status="postprocessing",
            current_stage="postprocessing",
        )

        t0 = time.monotonic()
        final_output_path = run_postprocessing(raw_output_path, result["garment_processed"])
        timing["postprocessing_ms"] = int((time.monotonic() - t0) * 1000)

        intermediates["colour_corrected"] = final_output_path
        await _repo.update_job(
            job_id,
            intermediate_outputs=json.dumps(intermediates),
        )

        # ── Completion ──────────────────────────────────────────────
        await _repo.update_job(
            job_id,
            status="complete",
            current_stage=None,
            result_image_path=final_output_path,
            completed_at=datetime.now(timezone.utc).isoformat(),
            preprocessing_ms=timing["preprocessing_ms"],
            inference_ms=timing["inference_ms"],
            postprocessing_ms=timing["postprocessing_ms"],
        )

    except Exception as e:
        await _repo.update_job(
            job_id,
            status="failed",
            error_message=str(e),
            current_stage=None,
            intermediate_outputs=json.dumps(intermediates) if intermediates else None,
        )
