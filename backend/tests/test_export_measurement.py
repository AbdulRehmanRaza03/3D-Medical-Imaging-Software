"""Tests for mesh export and measurements."""
from __future__ import annotations

import numpy as np
import pytest

from app.services import export_service, measurement_service, reconstruction_service


def _mesh():
    return reconstruction_service.MeshData(
        vertices=np.array(
            [[0., 0., 0.], [10., 0., 0.], [0., 10., 0.]], dtype=np.float32
        ),
        faces=np.array([[0, 1, 2]], dtype=np.int64),
        bbox_min=(0.0, 0.0, 0.0),
        bbox_max=(10.0, 10.0, 0.0),
        physical_size=(10.0, 10.0, 0.0),
        threshold_hu=300.0,
    )


def test_export_stl():
    data = export_service.export_stl(_mesh())
    assert data.startswith(b"solid") or b"STL" in data or len(data) > 80


def test_export_obj():
    data = export_service.export_obj(_mesh())
    text = data.decode("utf-8")
    assert "v " in text
    assert "f " in text


def test_export_glb():
    data = export_service.export_glb(_mesh())
    assert data[:4] == b"glTF"  # GLB magic


def test_export_bad_format_raises():
    with pytest.raises(Exception):
        export_service.export_mesh(_mesh(), "xyz")


def test_distance():
    d = measurement_service.distance_mm([0., 0., 0.], [10., 0., 0.])
    assert d == 10.0


def test_angle():
    a = measurement_service.angle_deg([10., 0., 0.], [0., 0., 0.], [0., 10., 0.])
    assert a == 90.0


def test_angle_requires_distinct_points():
    with pytest.raises(Exception):
        measurement_service.angle_deg([0., 0., 0.], [0., 0., 0.], [1., 1., 1.])
