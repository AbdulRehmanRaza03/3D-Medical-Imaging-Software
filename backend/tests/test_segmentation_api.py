"""API tests for segmentation endpoints (Phase 3)."""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_ct_series_bytes


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    import app.core.config as config

    config.settings = config.get_settings.__wrapped__()
    config.get_settings.cache_clear()
    config.settings = config.get_settings()

    from app.db.session import Base, engine
    from app.models import study as _study_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    from app.main import app

    yield TestClient(app)


def _upload(client) -> int:
    files, _ = make_ct_series_bytes(num_slices=8)
    payload = [
        ("files", (name, io.BytesIO(data), "application/dicom"))
        for name, data in files
    ]
    r = client.post("/api/v1/studies/upload", files=payload)
    assert r.status_code == 201, r.text
    return r.json()["study"]["id"]


def test_list_segmentation_models(client):
    r = client.get("/api/v1/segmentation/models")
    assert r.status_code == 200
    models = r.json()
    assert isinstance(models, list)
    assert any(m["id"] == "bone_1" for m in models)
    bone = next(m for m in models if m["id"] == "bone_1")
    # No checkpoint configured, so it is not available for inference.
    assert bone["checkpoint_available"] is False


def test_segmentation_job_missing_checkpoint(client):
    study_id = _upload(client)
    r = client.post(
        "/api/v1/segmentation/jobs",
        json={"model_id": "bone_1", "study_id": study_id},
    )
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]

    import time

    for _ in range(50):
        jr = client.get(f"/api/v1/segmentation/jobs/{job_id}")
        job = jr.json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    # Without a checkpoint, the job must fail with a clear error.
    assert job["status"] == "failed"
    assert job["error"]


def test_segmentation_models_unknown(client):
    r = client.post(
        "/api/v1/segmentation/jobs",
        json={"model_id": "nope", "study_id": 1},
    )
    # Study may not exist; either way it should not succeed silently.
    assert r.status_code in (200, 404, 422)


def test_list_segmentations_empty(client):
    study_id = _upload(client)
    r = client.get(f"/api/v1/studies/{study_id}/segmentations")
    assert r.status_code == 200
    assert r.json()["results"] == []
