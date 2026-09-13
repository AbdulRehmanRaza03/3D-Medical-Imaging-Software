"""Tests for the coordinate system (voxel ↔ world) and MPR extraction."""
from __future__ import annotations

import numpy as np
import pytest

from app.services import mpr_service
from app.services.coordinate_service import build_coordinate_system

# Identity orientation: direction = identity 3x3 → voxel axes = patient axes.
IDENTITY_DIR = (1, 0, 0, 0, 1, 0, 0, 0, 1)


def test_voxel_to_world_identity():
    cs = build_coordinate_system((0.7, 0.7, 2.0), (0.0, 0.0, 0.0), IDENTITY_DIR)
    x, y, z = cs.voxel_to_world((10.0, 5.0, 3.0))
    assert x == pytest.approx(10 * 0.7)
    assert y == pytest.approx(5 * 0.7)
    assert z == pytest.approx(3 * 2.0)


def test_world_to_voxel_roundtrip():
    cs = build_coordinate_system((0.7, 0.7, 2.0), (-10.0, 20.0, 5.0), IDENTITY_DIR)
    world = (3.0, -1.5, 9.0)
    vz, vy, vx = cs.world_to_voxel(world)  # returns (z, y, x)
    # Recover world from the fractional voxel indices.
    x2, y2, z2 = cs.voxel_to_world((vx, vy, vz))
    assert x2 == pytest.approx(world[0])
    assert y2 == pytest.approx(world[1])
    assert z2 == pytest.approx(world[2])


def test_non_isotropic_spacing_physical_correctness():
    """Ensure physical dimensions scale correctly for non-isotropic spacing."""
    cs = build_coordinate_system((0.7, 0.7, 2.0), (0.0, 0.0, 0.0), IDENTITY_DIR)
    # A voxel at index (1, 1, 1) should be at (0.7, 0.7, 2.0).
    x, y, z = cs.voxel_to_world((1.0, 1.0, 1.0))
    assert x == pytest.approx(0.7)
    assert y == pytest.approx(0.7)
    assert z == pytest.approx(2.0)


def test_singular_direction_rejected():
    with pytest.raises(ValueError):
        build_coordinate_system((1, 1, 1), (0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0))


# --- MPR ---

def _volume():
    # (depth=8, height=16, width=32) with a value gradient so planes differ.
    d, h, w = 8, 16, 32
    vol = np.zeros((d, h, w), dtype=np.float32)
    for z in range(d):
        vol[z] = z * 100.0 + np.arange(w, dtype=np.float32)[None, :]
    return vol


def test_axial_extraction_shape_and_values():
    vol = _volume()
    shape = (8, 16, 32)
    meta = mpr_service.plane_metadata(shape, (0.7, 0.7, 2.0), "axial")
    assert meta.total == 8
    assert meta.width == 32
    assert meta.height == 16

    sl = mpr_service.extract_plane(vol, "axial", 3)
    assert sl.shape == (16, 32)  # (height, width) = (rows=y, cols=x)
    # axial slice 3 should equal vol[3].
    assert np.allclose(sl, vol[3])


def test_coronal_extraction_shape_and_values():
    vol = _volume()
    shape = (8, 16, 32)
    meta = mpr_service.plane_metadata(shape, (0.7, 0.7, 2.0), "coronal")
    assert meta.total == 16  # one per row (y)
    assert meta.width == 32  # x
    assert meta.height == 8  # z

    sl = mpr_service.extract_plane(vol, "coronal", 5)
    assert sl.shape == (8, 32)  # (rows=z, cols=x)
    # coronal at y=5 should equal vol[:, 5, :].
    assert np.allclose(sl, vol[:, 5, :])


def test_sagittal_extraction_shape_and_values():
    vol = _volume()
    shape = (8, 16, 32)
    meta = mpr_service.plane_metadata(shape, (0.7, 0.7, 2.0), "sagittal")
    assert meta.total == 32  # one per column (x)
    assert meta.width == 16  # y
    assert meta.height == 8  # z

    sl = mpr_service.extract_plane(vol, "sagittal", 3)
    assert sl.shape == (8, 16)  # (rows=z, cols=y)
    assert np.allclose(sl, vol[:, :, 3])


def test_mpr_out_of_range_raises():
    vol = _volume()
    with pytest.raises(Exception):
        mpr_service.extract_plane(vol, "axial", 99)
    with pytest.raises(Exception):
        mpr_service.extract_plane(vol, "coronal", -1)


def test_unknown_plane_raises():
    vol = _volume()
    with pytest.raises(Exception):
        mpr_service.extract_plane(vol, "oblique", 0)


def test_plane_physical_sizes_non_isotropic():
    shape = (8, 16, 32)  # (depth, height, width)
    spacing = (0.7, 0.7, 2.0)  # (sx, sy, sz)
    axial = mpr_service.plane_metadata(shape, spacing, "axial")
    assert axial.physical_width == pytest.approx(32 * 0.7)
    assert axial.physical_height == pytest.approx(16 * 0.7)

    coronal = mpr_service.plane_metadata(shape, spacing, "coronal")
    assert coronal.physical_width == pytest.approx(32 * 0.7)
    assert coronal.physical_height == pytest.approx(8 * 2.0)  # z uses thick spacing

    sagittal = mpr_service.plane_metadata(shape, spacing, "sagittal")
    assert sagittal.physical_width == pytest.approx(16 * 0.7)
    assert sagittal.physical_height == pytest.approx(8 * 2.0)
