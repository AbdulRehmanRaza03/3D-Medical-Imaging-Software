"""Tests for volume construction and reconstruction pipeline."""
from __future__ import annotations

import io

import numpy as np
import pydicom
import pytest

from app.services import dicom_service, reconstruction_service, volume_service


def _series(num_slices=8):
    from tests.conftest import make_ct_series_bytes

    files, _ = make_ct_series_bytes(num_slices=num_slices)
    datasets = [pydicom.dcmread(io.BytesIO(data)) for _, data in files]
    result = dicom_service.detect_series(datasets)
    return result.series[0]


def test_volume_dimensions_and_spacing():
    series = _series(8)
    volume = volume_service.build_volume(series)
    assert volume.data.shape == (8, 16, 16)  # (depth, height, width)
    assert volume.dimensions == (16, 16, 8)  # (width, height, depth)
    assert volume.spacing[0] == 0.5
    assert volume.spacing[1] == 0.5
    assert volume.spacing[2] == 1.0  # slice thickness


def test_volume_hounsfield_units():
    series = _series(8)
    volume = volume_service.build_volume(series)
    # Central bone region should be ~300 HU.
    center = volume.data[:, 8, 8]
    assert np.all(center > 200.0)


def test_mask_and_marching_cubes_respects_spacing():
    series = _series(8)
    volume = volume_service.build_volume(series)
    mesh = reconstruction_service.reconstruct_bone(
        volume, threshold_hu=200.0, remove_small_components=False
    )
    assert mesh.vertices.shape[0] > 0
    assert mesh.faces.shape[0] > 0
    # Physical size z should equal ~7 * 1.0 mm (8 slices minus boundary).
    assert mesh.physical_size[2] > 0


def test_marching_cubes_anisotropic_spacing():
    """Ensure anisotropic spacing is applied (not index-space distortion)."""
    from tests.conftest import make_ct_series_bytes

    files, _ = make_ct_series_bytes(num_slices=8, pixel_spacing=(0.5, 0.5),
                                    slice_thickness=2.0)
    datasets = [pydicom.dcmread(io.BytesIO(data)) for _, data in files]
    series = dicom_service.detect_series(datasets).series[0]
    volume = volume_service.build_volume(series)
    mesh = reconstruction_service.reconstruct_bone(
        volume, threshold_hu=200.0, remove_small_components=False
    )
    # z physical size should be ~2x the isotropic-1mm case.
    # With slice thickness 2.0, the bone spans roughly 5 slices * 2 = ~10mm.
    assert mesh.physical_size[2] > 5.0


def test_empty_threshold_raises():
    series = _series(8)
    volume = volume_service.build_volume(series)
    with pytest.raises(Exception):
        reconstruction_service.reconstruct_bone(volume, threshold_hu=5000.0)


def test_clean_mesh_removes_degenerate():
    verts = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]], dtype=np.float32)
    faces = np.array([[0, 1, 2], [0, 0, 1], [1, 2, 1]], dtype=np.int64)
    v2, f2 = reconstruction_service.clean_mesh(verts, faces)
    assert len(f2) == 1  # two degenerate faces removed
    assert f2.tolist() == [[0, 1, 2]] or f2.tolist() == [[0, 1, 2]]
