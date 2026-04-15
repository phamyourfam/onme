"""Try-on job persistence backed by PostgreSQL via SQLAlchemy."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update

from api.database import AsyncSessionFactory
from api.db.models import TryOnJobORM
from api.models import Job


def _as_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _decode_intermediates(
    intermediate_outputs: str | None,
) -> dict[str, object] | None:
    if intermediate_outputs is None:
        return None
    return json.loads(intermediate_outputs)


def _encode_intermediates(
    intermediate_assets: dict[str, object] | None,
) -> str | None:
    if intermediate_assets is None:
        return None
    return json.dumps(intermediate_assets)


def _to_job(model: TryOnJobORM) -> Job:
    return Job(
        id=model.id.hex,
        status=model.status,
        model_name=model.model_name,
        person_image_path=model.person_asset_url,
        garment_image_path=model.garment_asset_url,
        result_image_path=model.result_asset_url,
        intermediate_outputs=_encode_intermediates(model.intermediate_assets),
        error_message=model.error_message,
        current_stage=model.current_stage,
        created_at=model.created_at.isoformat(),
        completed_at=model.completed_at.isoformat()
        if model.completed_at
        else None,
        preprocessing_ms=model.preprocessing_ms,
        inference_ms=model.inference_ms,
        postprocessing_ms=model.postprocessing_ms,
        user_id=model.user_id.hex if model.user_id else None,
    )


class JobRepository:
    """PostgreSQL repository for try-on jobs."""

    async def create_job(self, job: Job) -> None:
        async with AsyncSessionFactory() as session:
            model = TryOnJobORM(
                id=_as_uuid(job.id),
                status=job.status,
                model_name=job.model_name,
                person_asset_url=job.person_image_path,
                garment_asset_url=job.garment_image_path,
                result_asset_url=job.result_image_path,
                intermediate_assets=_decode_intermediates(job.intermediate_outputs),
                error_message=job.error_message,
                current_stage=job.current_stage,
                created_at=_to_datetime(job.created_at) or datetime.now(timezone.utc),
                completed_at=_to_datetime(job.completed_at),
                preprocessing_ms=job.preprocessing_ms,
                inference_ms=job.inference_ms,
                postprocessing_ms=job.postprocessing_ms,
                user_id=_as_uuid(job.user_id) if job.user_id else None,
            )
            session.add(model)
            await session.commit()

    async def get_job(self, job_id: str) -> Job | None:
        async with AsyncSessionFactory() as session:
            model = await session.get(TryOnJobORM, _as_uuid(job_id))
        if model is None:
            return None
        return _to_job(model)

    async def update_job_status(self, job_id: str, status: str) -> None:
        async with AsyncSessionFactory() as session:
            await session.execute(
                update(TryOnJobORM)
                .where(TryOnJobORM.id == _as_uuid(job_id))
                .values(status=status)
            )
            await session.commit()

    async def update_job(self, job_id: str, **fields: object) -> None:
        if not fields:
            return

        if "person_image_path" in fields:
            fields["person_asset_url"] = fields.pop("person_image_path")
        if "garment_image_path" in fields:
            fields["garment_asset_url"] = fields.pop("garment_image_path")
        if "result_image_path" in fields:
            fields["result_asset_url"] = fields.pop("result_image_path")
        if "intermediate_outputs" in fields:
            fields["intermediate_assets"] = _decode_intermediates(
                fields.pop("intermediate_outputs")
            )
        if "completed_at" in fields:
            fields["completed_at"] = _to_datetime(fields["completed_at"])
        if "queued_at" in fields:
            fields["queued_at"] = _to_datetime(fields["queued_at"])
        if "user_id" in fields and fields["user_id"] is not None:
            fields["user_id"] = _as_uuid(str(fields["user_id"]))

        async with AsyncSessionFactory() as session:
            await session.execute(
                update(TryOnJobORM)
                .where(TryOnJobORM.id == _as_uuid(job_id))
                .values(**fields)
            )
            await session.commit()

    async def get_jobs_by_user(self, user_id: str) -> list[Job]:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(TryOnJobORM)
                .where(TryOnJobORM.user_id == _as_uuid(user_id))
                .order_by(TryOnJobORM.created_at.desc())
            )
            models = result.scalars().all()

        return [_to_job(model) for model in models]
