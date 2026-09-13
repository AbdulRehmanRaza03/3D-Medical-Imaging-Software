"""API tests for MPR and coordinate endpoints."""
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
    files, _ = make_ct_series_bytes(num_slices=8, slice_thickness=2.0)
    payload = [
        ("files", (name, io.BytesIO(data), "application/dicom"))
        for name, data in files
    ]
    r = client.post("/api/v1/studies/upload", files=payload)
    assert r.status_code == 201, r.text
    return r.json()["study"]["id"]


def test_volume_info(client):
    study_id = _upload(client)
    r = client.get(f"/api/v1/studies/{study_id}/volume")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["shape"] == [8, 16, 16]  # depth, height, width
    assert body["spacing"] == [0.5, 0.5, 2.0]
    assert len(body["direction"]) == 9


def test_mpr_all_planes(client):
    study_id = _upload(client)

    axial = client.get(f"/api/v1/studies/{study_id}/mpr/axial?index=3")
    assert axial.status_code == 200, axial.text
    assert axial.json()["plane"] == "axial"
    assert axial.json()["total"] == 8
    assert "image_base64" in axial.json()

    coronal = client.get(f"/api/v1/studies/{study_id}/mpr/coronal?index=5")
    assert coronal.status_code == 200
    assert coronal.json()["total"] == 16  # one per row

    sagittal = client.get(f"/api/v1/studies/{study_id}/mpr/sagittal?index=5")
    assert sagittal.status_code == 200
    assert sagittal.json()["total"] == 16  # one per column


def test_mpr_invalid_plane(client):
    study_id = _upload(client)
    r = client.get(f"/api/v1/studies/{study_id}/mpr/oblique?index=0")
    assert r.status_code == 400
    assert r.json()["code"] == "bad_plane"


def test_mpr_out_of_range(client):
    study_id = _upload(client)
    r = client.get(f"/api/v1/studies/{study_id}/mpr/axial?index=999")
    assert r.status_code == 400
    assert r.json()["code"] == "slice_out_of_range"


def test_coordinates_endpoint(client):
    study_id = _upload(client)
    # Physical (x=4.0, y=4.0, z=4.0) with spacing (0.5,0.5,2.0) → voxel (8,8,2).
    r = client.get(
        f"/api/v1/studies/{study_id}/coordinates",
        params={"x": 4.0, "y": 4.0, "z": 4.0},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["world"] == [4.0, 4.0, 4.0]
    assert "hu" in body
    assert isinstance(body["hu"], float)


def test_voxel_endpoint(client):
    study_id = _upload(client)
    r = client.get(
        f"/api/v1/studies/{study_id}/voxel",
        params={"x": 8, "y": 8, "z": 4},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["index"] == [8, 8, 4]
    assert len(body["world"]) == 3
    assert "hu" in body


def test_voxel_out_of_range(client):
    study_id = _upload(client)
    r = client.get(
        f"/api/v1/studies/{study_id}/voxel",
        params={"x": 999, "y": 0, "z": 0},
    )
    assert r.status_code == 400
