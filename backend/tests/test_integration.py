"""End-to-end integration test: real DICOM -> volume -> reconstruction -> mesh -> export."""
from __future__ import annotations

import io

import numpy as np
import pydicom

from app.services import (
    dicom_service,
    export_service,
    reconstruction_service,
    volume_service,
)
from tests.conftest import make_ct_series_bytes


def test_full_pipeline_integration():
    files, series_uid = make_ct_series_bytes(num_slices=12, slice_thickness=1.5)

    # 1. Parse DICOM.
    datasets = [pydicom.dcmread(io.BytesIO(data)) for _, data in files]

    # 2. Detect + order series.
    result = dicom_service.detect_series(datasets)
    series = result.series[0]
    assert series.slice_count == 12
    assert series.series_uid == series_uid

    # 3. Build volume (HU, spacing preserved).
    volume = volume_service.build_volume(series)
    assert volume.data.shape == (12, 16, 16)
    assert volume.spacing == (0.5, 0.5, 1.5)

    # 4. Reconstruct bone surface.
    mesh = reconstruction_service.reconstruct_bone(
        volume, threshold_hu=200.0, remove_small_components=False
    )
    assert mesh.vertices.shape[0] > 0
    assert mesh.faces.shape[0] > 0
    assert mesh.physical_size[2] > 5.0  # ~ (12-2) * 1.5mm

    # 5. Export to all three formats.
    stl = export_service.export_stl(mesh)
    obj = export_service.export_obj(mesh)
    glb = export_service.export_glb(mesh)
    assert len(stl) > 80
    assert b"v " in obj
    assert glb[:4] == b"glTF"
