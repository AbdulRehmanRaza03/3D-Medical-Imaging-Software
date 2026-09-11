"""Volume construction: CT intensity (HU) conversion and 3D volume assembly.

Produces a spatially-aware 3D volume from an ordered set of DICOM slices. The
result preserves width, height, depth, voxel spacing, origin and orientation so
that downstream reconstruction yields physically accurate geometry.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.core.exceptions import ProcessingError
from app.services.dicom_service import SeriesInfo, _as_float_tuple, _safe_tag


@dataclass
class Volume:
    """A 3D medical image volume with full spatial metadata."""

    data: np.ndarray  # shape (depth, height, width), float32 HU
    spacing: tuple[float, float, float]  # (x, y, z) in mm
    origin: tuple[float, float, float]  # (x, y, z) in mm
    direction: tuple[float, ...]  # 9-element direction cosine matrix (row-major)
    dimensions: tuple[int, int, int]  # (width, height, depth)

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.data.shape

    @property
    def hu_min(self) -> float:
        return float(np.min(self.data))

    @property
    def hu_max(self) -> float:
        return float(np.max(self.data))


def apply_rescale(pixel_array: np.ndarray, slope: float, intercept: float) -> np.ndarray:
    """Apply DICOM RescaleSlope/Intercept to convert to Hounsfield Units."""
    return pixel_array.astype(np.float32) * slope + intercept


def build_volume(series: SeriesInfo) -> Volume:
    """Assemble a 3D volume from a sorted series.

    Slices must already be anatomically ordered (see ``dicom_service``). The
    pixel arrays are stacked along the depth axis and converted to HU.
    """
    if not series.slices:
        raise ProcessingError("Series has no slices to build a volume from.")

    rows = series.rows
    columns = series.columns
    if rows is None or columns is None:
        raise ProcessingError("Series is missing Rows/Columns metadata.")

    slope = series.rescale_slope if series.rescale_slope is not None else 1.0
    intercept = series.rescale_intercept if series.rescale_intercept is not None else 0.0

    depth = len(series.slices)
    buffer = np.empty((depth, rows, columns), dtype=np.float32)

    for i, sl in enumerate(series.slices):
        px = sl.dataset.pixel_array
        if px.shape != (rows, columns):
            raise ProcessingError(
                f"Slice {i} has unexpected shape {px.shape}; expected {(rows, columns)}."
            )
        buffer[i] = apply_rescale(px, slope, intercept)

    # Spacing (x, y, z). z-spacing derived from slice positions or thickness.
    ps = series.pixel_spacing
    sx = float(ps[0]) if ps and ps[0] else 1.0
    sy = float(ps[1]) if ps and ps[1] else 1.0
    sz = _derive_slice_spacing(series)

    # Origin: first slice ImagePositionPatient (or zeros).
    origin = _derive_origin(series)

    # Direction: full 3x3 row-major direction cosines.
    direction = _derive_direction(series)

    return Volume(
        data=buffer,
        spacing=(sx, sy, sz),
        origin=origin,
        direction=direction,
        dimensions=(columns, rows, depth),
    )


def _derive_slice_spacing(series: SeriesInfo) -> float:
    if series.slice_spacing:
        return float(series.slice_spacing)
    if len(series.slices) >= 2:
        keys = np.array([s.sort_key for s in series.slices], dtype=float)
        diffs = np.abs(np.diff(keys))
        diffs = diffs[diffs != 0]
        if diffs.size > 0:
            return float(np.median(diffs))
    if series.slice_thickness is not None:
        return float(series.slice_thickness)
    return 1.0


def _derive_origin(series: SeriesInfo) -> tuple[float, float, float]:
    pos = series.slices[0].image_position
    if pos is not None and len(pos) >= 3:
        return (float(pos[0]), float(pos[1]), float(pos[2]))
    return (0.0, 0.0, 0.0)


def _derive_direction(series: SeriesInfo) -> tuple[float, ...]:
    """Build a 3x3 row-major direction matrix from DICOM orientation.

    DICOM stores two direction cosines (row and column). The third axis (slice
    normal) is the cross product, giving a full orthonormal basis for the volume.
    """
    orient = series.image_orientation
    identity = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    if orient is None or len(orient) < 6:
        return identity

    row_cos = np.array(orient[0:3], dtype=float)
    col_cos = np.array(orient[3:6], dtype=float)
    normal = np.cross(row_cos, col_cos)
    norm = np.linalg.norm(normal)
    if norm <= 0:
        return identity
    normal = normal / norm

    # Row-major 3x3: [row_cos; col_cos; normal]
    direction = np.array(
        [
            row_cos[0], row_cos[1], row_cos[2],
            col_cos[0], col_cos[1], col_cos[2],
            normal[0], normal[1], normal[2],
        ],
        dtype=float,
    )
    return tuple(float(v) for v in direction)
