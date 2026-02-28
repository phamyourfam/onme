"""
Data-access layer for Job persistence using raw SQLite.
"""

import sqlite3

from database import get_connection
from models import Job


class JobRepository:
    """Raw-SQL repository for the ``jobs`` table."""

    def create_job(self, job: Job) -> None:
        """Insert a new job row into the database."""
        conn = get_connection()
        try:
            with conn:  
                conn.execute(
                    """
                    INSERT INTO jobs (
                        id, status, model_name,
                        person_image_path, garment_image_path,
                        result_image_path, intermediate_outputs,
                        error_message, current_stage,
                        created_at, completed_at,
                        preprocessing_ms, inference_ms, postprocessing_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.id,
                        job.status,
                        job.model_name,
                        job.person_image_path,
                        job.garment_image_path,
                        job.result_image_path,
                        job.intermediate_outputs,
                        job.error_message,
                        job.current_stage,
                        job.created_at,
                        job.completed_at,
                        job.preprocessing_ms,
                        job.inference_ms,
                        job.postprocessing_ms,
                    ),
                )
        finally:
            conn.close()

    def get_job(self, job_id: str) -> Job | None:
        """Fetch a single job by its ID, or ``None`` if not found."""
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return None
        return Job(**dict(row))

    def update_job_status(self, job_id: str, status: str) -> None:
        """Update the status column for the given job."""
        conn = get_connection()
        try:
            with conn:  
                conn.execute(
                    "UPDATE jobs SET status = ? WHERE id = ?",
                    (status, job_id),
                )
        finally:
            conn.close()
