"""Unit tests for api.repository.JobRepository."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from api.database import init_db
from api.models import Job
from api.repository import JobRepository


@pytest.fixture(autouse=True)
def _tmp_database(tmp_path):
    """Redirect the database to a temporary directory for each test."""
    db_path = str(tmp_path / "test.db")
    with patch("api.database.settings") as mock_settings:
        mock_settings.DATABASE_PATH = db_path
        init_db()
        yield


@pytest.fixture()
def repo():
    return JobRepository()


def _make_job(**overrides) -> Job:
    defaults = {
        "id": "job-1",
        "status": "pending",
        "model_name": "idm-vton",
        "person_image_path": "uploads/person.jpg",
        "garment_image_path": "uploads/garment.jpg",
    }
    defaults.update(overrides)
    return Job(**defaults)


def test_create_and_retrieve(repo):
    job = _make_job()
    repo.create_job(job)
    fetched = repo.get_job("job-1")
    assert fetched is not None
    assert fetched.id == "job-1"
    assert fetched.status == "pending"
    assert fetched.model_name == "idm-vton"
    assert fetched.person_image_path == "uploads/person.jpg"
    assert fetched.garment_image_path == "uploads/garment.jpg"


def test_get_nonexistent(repo):
    result = repo.get_job("does-not-exist")
    assert result is None


def test_update_changes_status(repo):
    job = _make_job()
    repo.create_job(job)
    repo.update_job_status("job-1", "complete")
    fetched = repo.get_job("job-1")
    assert fetched is not None
    assert fetched.status == "complete"


def test_update_stores_intermediates(repo):
    job = _make_job()
    repo.create_job(job)
    intermediates = json.dumps({"preprocessing": "uploads/pre.jpg"})
    repo.update_job("job-1", intermediate_outputs=intermediates)
    fetched = repo.get_job("job-1")
    assert fetched is not None
    assert fetched.intermediate_outputs is not None
    parsed = json.loads(fetched.intermediate_outputs)
    assert parsed["preprocessing"] == "uploads/pre.jpg"
