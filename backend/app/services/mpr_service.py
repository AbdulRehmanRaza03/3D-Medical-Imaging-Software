"""Multiplanar reconstruction (MPR) from a single 3D CT volume.

Extracts the three standard anatomical planes — axial, coronal, sagittal — from
the SAME in-memory volume array. No separate copies of the dataset are made;
each plane is a view (a 2D slice through one axis) of the shared 3D data.

Plane mapping (volume array is ``data[z, y, x]``):

* Axial    → slice along axis 0 (z): ``data[z, :, :]``
* Coronal  → slice along axis 1 (y): ``data[:, y, :]``
* Sagittal → slice along axis 2 (x): ``data[:, :, x]``

This is *true* MPR — the same voxels are simply re-sliced along a different
axis, so all views are spatially consistent with the original volume.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.core.exceptions import ProcessingError

PLANES = ("axial", "coronal", "sagittal")


@dataclass(frozen=True)
class PlaneMetadata:
    """Metadata describing the dimensions and axis order of one MPR plane."""

    name: str
    total: int  # number of slices along this axis
    width: int  # image width in pixels
    height: int  # image height in pixels
    physical_width: float  # mm
    physical_height: float  # mm
    axis: int  # volume axis to slice along (0=z axial, 1=y coronal, 2=x sagittal)


def plane_metadata(
    shape: tuple[int, int, int],  # (depth, height, width)
    spacing: tuple[float, float, float],  # (sx, sy, sz)
    plane: str,
) -> PlaneMetadata:
    """Compute dimensions and physical sizes for a plane."""
    depth, height, width = shape
    sx, sy, sz = spacing

    if plane == "axial":
        return PlaneMetadata("axial", depth, width, height, width * sx, height * sy, 0)
    if plane == "coronal":
        return PlaneMetadata("coronal", height, width, depth, width * sx, depth * sz, 1)
    if plane == "sagittal":
        return PlaneMetadata("sagittal", width, height, depth, height * sy, depth * sz, 2)
    raise ProcessingError(f"Unknown plane: {plane}", code="bad_plane")


def extract_plane(
    data: np.ndarray,  # (depth, height, width) HU volume
    plane: str,
    slice_index: int,
) -> np.ndarray:
    """Return a 2D HU slice for the requested plane and index.

    The returned array is a contiguous 2D view along one volume axis. Display
    orientation (rows = vertical, cols = horizontal) follows the anatomical
    convention of each plane:

    * axial    (z const): rows = y (anterior→posterior), cols = x (left→right)
    * coronal  (y const): rows = z (inferior→superior),  cols = x (left→right)
    * sagittal (x const): rows = z (inferior→superior),  cols = y (anterior→posterior)

    All three planes are simply re-slices of the same underlying volume — no
    interpolation or duplication is performed.
    """
    if data.ndim != 3:
        raise ProcessingError("Volume must be a 3D array.", code="bad_volume")

    depth, height, width = data.shape

    if plane == "axial":
        if slice_index < 0 or slice_index >= depth:
            raise ProcessingError(f"Slice {slice_index} out of range for axial.", code="slice_out_of_range")
        # data[z, y, x] already has rows=y, cols=x.
        return np.ascontiguousarray(data[slice_index, :, :])

    if plane == "coronal":
        if slice_index < 0 or slice_index >= height:
            raise ProcessingError(f"Slice {slice_index} out of range for coronal.", code="slice_out_of_range")
        # data[:, y, :] → (depth, width) = rows=z, cols=x.
        return np.ascontiguousarray(data[:, slice_index, :])

    if plane == "sagittal":
        if slice_index < 0 or slice_index >= width:
            raise ProcessingError(f"Slice {slice_index} out of range for sagittal.", code="slice_out_of_range")
        # data[:, :, x] → (depth, height) = rows=z, cols=y.
        return np.ascontiguousarray(data[:, :, slice_index])

    raise ProcessingError(f"Unknown plane: {plane}", code="bad_plane")


def volume_shape(data: np.ndarray) -> tuple[int, int, int]:
    """Return (depth, height, width) of a 3D volume."""
    if data.ndim != 3:
        raise ProcessingError("Volume must be a 3D array.", code="bad_volume")
    return data.shape
