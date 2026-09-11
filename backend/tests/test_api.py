"""API tests using FastAPI TestClient with a temporary SQLite database."""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_ct_series_bytes


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    # Import after env override so settings pick up the temp paths.
    import app.core.config as config

    config.settings = config.get_settings.__wrapped__()  # re-evaluate
    config.get_settings.cache_clear()
    config.settings = config.get_settings()

    from app.db.session import Base, engine
    from app.models import study as _study_models  # noqa: F401 (register models)

    Base.metadata.create_all(bind=engine)

    from app.main import app

    client = TestClient(app)
    yield client


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_and_get_study(client):
    files, _ = make_ct_series_bytes(num_slices=6)
    payload = [
        ("files", (name, io.BytesIO(data), "application/dicom"))
        for name, data in files
    ]
    r = client.post("/api/v1/studies/upload", files=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    study = data["study"]
    assert study["id"] > 0
    assert study["modality"] == "CT"
    assert study["slice_count"] == 6

    # Get study detail.
    r2 = client.get(f"/api/v1/studies/{study['id']}")
    assert r2.status_code == 200
    assert len(r2.json()["series"]) >= 1


def test_invalid_file_returns_error(client):
    payload = [
        ("files", ("bad.txt", io.BytesIO(b"hello world"), "text/plain")),
    ]
    r = client.post("/api/v1/studies/upload", files=payload)
    assert r.status_code == 422


def test_slice_endpoint(client):
    files, _ = make_ct_series_bytes(num_slices=6)
    payload = [
        ("files", (name, io.BytesIO(data), "application/dicom"))
        for name, data in files
    ]
    client.post("/api/v1/studies/upload", files=payload)
    study_id = client.get("/api/v1/studies").json()["studies"][0]["id"]

    r = client.get(f"/api/v1/studies/{study_id}/slice/0")
    assert r.status_code == 200
    body = r.json()
    assert body["index"] == 0
    assert body["total"] == 6
    assert "image_base64" in body


def test_reconstruct_and_model(client):
    files, _ = make_ct_series_bytes(num_slices=10)
    payload = [
        ("files", (name, io.BytesIO(data), "application/dicom"))
        for name, data in files
    ]
    client.post("/api/v1/studies/upload", files=payload)
    study_id = client.get("/api/v1/studies").json()["studies"][0]["id"]

    r = client.post(
        f"/api/v1/studies/{study_id}/reconstruct",
        json={"threshold_hu": 200.0, "remove_small_components": False},
    )
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]

    # Poll job until completed.
    import time

    for _ in range(100):
        jr = client.get(f"/api/v1/jobs/{job_id}")
        assert jr.status_code == 200
        job = jr.json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    assert job["status"] == "completed", job
    assert job["result_model_id"] is not None

    # List models.
    mr = client.get(f"/api/v1/studies/{study_id}/models")
    assert mr.status_code == 200
    models = mr.json()["models"]
    assert len(models) >= 1
    model = models[0]
    assert model["vertices"] > 0
    assert model["triangles"] > 0

    # Export.
    er = client.get(f"/api/v1/models/{model['id']}/export/stl")
    assert er.status_code == 200
    assert len(er.content) > 80
