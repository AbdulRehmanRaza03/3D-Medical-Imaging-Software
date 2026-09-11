"""Standalone end-to-end verification of the full Phase 1 workflow.

Uses FastAPI TestClient with real (synthetic) DICOM through:
  upload -> study -> metadata -> slice -> reconstruct -> model -> export.
"""
from __future__ import annotations

import io
import os
import tempfile
import time

from fastapi.testclient import TestClient

# Point storage/db at a temp dir before importing app.
tmp = tempfile.mkdtemp()
os.environ["STORAGE_DIR"] = os.path.join(tmp, "storage")
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/verify.db"

from app.main import app  # noqa: E402
from app.db.session import init_db  # noqa: E402
from tests.conftest import make_ct_series_bytes  # noqa: E402

init_db()
client = TestClient(app)


def main() -> None:
    print("== OrthoVision AI end-to-end verification ==\n")

    # 1. Health.
    r = client.get("/health")
    assert r.status_code == 200, r.text
    print("[1] Health OK:", r.json())

    # 2. Upload.
    files, _ = make_ct_series_bytes(num_slices=20, rows=64, columns=64, slice_thickness=1.0)
    payload = [(f"files", (name, io.BytesIO(data), "application/dicom")) for name, data in files]
    r = client.post("/api/v1/studies/upload", files=payload)
    assert r.status_code == 201, r.text
    study = r.json()["study"]
    study_id = study["id"]
    print(f"[2] Upload OK: study id={study_id}, modality={study['modality']}, "
          f"slices={study['slice_count']}, series={study['series_count']}")

    # 3. Metadata.
    r = client.get(f"/api/v1/studies/{study_id}/metadata")
    assert r.status_code == 200, r.text
    meta = r.json()
    print(f"[3] Metadata OK: rows={meta['rows']}, cols={meta['columns']}, "
          f"spacing={meta['pixel_spacing']}, physical={meta['physical_size']}")

    # 4. Slice.
    r = client.get(f"/api/v1/studies/{study_id}/slice/5")
    assert r.status_code == 200, r.text
    sl = r.json()
    print(f"[4] Slice OK: index={sl['index']}, total={sl['total']}, "
          f"png_bytes={len(sl['image_base64'])} (base64)")

    # 5. Reconstruct.
    r = client.post(
        f"/api/v1/studies/{study_id}/reconstruct",
        json={"threshold_hu": 200.0, "remove_small_components": False},
    )
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]
    print(f"[5] Reconstruction job submitted: {job_id}")

    # 6. Poll job.
    job = None
    for _ in range(150):
        jr = client.get(f"/api/v1/jobs/{job_id}")
        job = jr.json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.2)
    assert job and job["status"] == "completed", job
    model_id = job["result_model_id"]
    print(f"[6] Job completed: model_id={model_id}, progress={job['progress']}")

    # 7. Model stats.
    mr = client.get(f"/api/v1/studies/{study_id}/models")
    model = mr.json()["models"][0]
    print(f"[7] Model OK: vertices={model['vertices']}, triangles={model['triangles']}, "
          f"physical_size={model['physical_size']}")

    # 8. Export (all three formats).
    for fmt in ("stl", "obj", "glb"):
        er = client.get(f"/api/v1/models/{model_id}/export/{fmt}")
        assert er.status_code == 200, er.text
        print(f"[8] Export {fmt.upper()} OK: {len(er.content)} bytes")

    # 9. Measurement.
    mer = client.post(
        f"/api/v1/models/{model_id}/measurements",
        json={"points": [[0, 0, 0], [10, 0, 0]], "measurement_type": "distance"},
    )
    assert mer.status_code == 200, mer.text
    m = mer.json()["measurement"]
    print(f"[9] Measurement OK: {m['value']:.2f} {m['unit']}")

    print("\n== ALL CHECKS PASSED ==")


if __name__ == "__main__":
    main()
