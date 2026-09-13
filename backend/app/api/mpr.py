"""MPR (multiplanar reconstruction) API endpoints.

Serves axial/coronal/sagittal slice images, volume metadata, and voxel
inspection (physical coordinate + HU value) — all derived from the single
stored CT volume. No new per-plane copies of the dataset are created.
"""
from __future__ import annotations

import base64
import io

import numpy as np
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from PIL import Image
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ProcessingError, ValidationError
from app.db.session import get_db
from app.models.study import Study
from app.services import mpr_service, study_service, windowing_service
from app.services.coordinate_service import build_coordinate_system

router = APIRouter(prefix="/studies", tags=["mpr"])


def _load_volume(study_id: int):
    study = None
    # The caller validates existence separately; here we only load.
    return study_service.load_volume(study_id)


def _validate_study(db: Session, study_id: int) -> Study:
    study = db.get(Study, study_id)
    if study is None:
        raise NotFoundError("Study not found.", code="study_not_found")
    return study


@router.get("/{study_id}/volume")
def volume_info(study_id: int, db: Session = Depends(get_db)):
    """Return volume spatial metadata (shape, spacing, origin, direction).

    This is the lightweight information the frontend needs to set up the MPR
    coordinate system without downloading the full (large) volume.
    """
    _validate_study(db, study_id)
    vol = _load_volume(study_id)
    data = vol["data"]
    depth, height, width = data.shape

    return {
        "shape": [depth, height, width],  # z, y, x
        "dimensions": [width, height, depth],  # x, y, z
        "spacing": [float(v) for v in vol["spacing"]],
        "origin": [float(v) for v in vol["origin"]],
        "direction": [float(v) for v in vol["direction"]],
        "hu_min": float(np.min(data)),
        "hu_max": float(np.max(data)),
    }


@router.get("/{study_id}/mpr/{plane}")
def get_mpr_slice(
    study_id: int,
    plane: str,
    index: int,
    width: float | None = None,
    level: float | None = None,
    db: Session = Depends(get_db),
):
    """Return a windowed 8-bit PNG slice for a given MPR plane.

    ``plane`` is one of ``axial`` | ``coronal`` | ``sagittal``.
    """
    _validate_study(db, study_id)
    if plane not in mpr_service.PLANES:
        raise ValidationError(f"Unknown plane '{plane}'.", code="bad_plane")

    vol = _load_volume(study_id)
    data = vol["data"]
    spacing = tuple(float(v) for v in vol["spacing"])

    meta = mpr_service.plane_metadata(data.shape, spacing, plane)
    if index < 0 or index >= meta.total:
        raise ValidationError(
            f"Slice index {index} out of range for {plane} (0..{meta.total - 1}).",
            code="slice_out_of_range",
        )

    hu_slice = mpr_service.extract_plane(data, plane, index)

    if width is None or level is None:
        width, level = windowing_service.default_window(
            float(np.min(data)), float(np.max(data))
        )

    display = windowing_service.apply_window(hu_slice, width, level)

    img = Image.fromarray(display, mode="L")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")

    return JSONResponse(
        content={
            "plane": plane,
            "index": index,
            "total": meta.total,
            "width": width,
            "level": level,
            "rows": int(display.shape[0]),
            "columns": int(display.shape[1]),
            "physical_width": meta.physical_width,
            "physical_height": meta.physical_height,
            "image_base64": encoded,
        }
    )


@router.get("/{study_id}/coordinates")
def get_coordinates(
    study_id: int,
    x: float = Query(..., description="physical X (mm)"),
    y: float = Query(..., description="physical Y (mm)"),
    z: float = Query(..., description="physical Z (mm)"),
    db: Session = Depends(get_db),
):
    """Map physical (world) coordinates to voxel index + nearby HU intensity.

    Used by the synchronous crosshair to translate a 3D point into the correct
    slice for each plane and to report the voxel intensity.
    """
    _validate_study(db, study_id)
    vol = _load_volume(study_id)
    data = vol["data"]
    depth, height, width = data.shape

    cs = build_coordinate_system(
        tuple(float(v) for v in vol["spacing"]),
        tuple(float(v) for v in vol["origin"]),
        tuple(float(v) for v in vol["direction"]),
    )

    # world (x,y,z) → voxel (z,y,x)
    vz, vy, vx = cs.world_to_voxel((x, y, z))

    # Round to nearest integer index and clamp to volume bounds.
    iz = int(round(vz))
    iy = int(round(vy))
    ix = int(round(vx))
    iz_clamped = max(0, min(depth - 1, iz))
    iy_clamped = max(0, min(height - 1, iy))
    ix_clamped = max(0, min(width - 1, ix))

    hu = float(data[iz_clamped, iy_clamped, ix_clamped])

    return {
        "voxel": [vx, vy, vz],  # fractional (x, y, z)
        "index": [ix, iy, iz],  # integer (x, y, z) = (column, row, slice)
        "clamped_index": [ix_clamped, iy_clamped, iz_clamped],
        "world": [x, y, z],
        "hu": hu,
        "in_bounds": (
            0 <= iz < depth and 0 <= iy < height and 0 <= ix < width
        ),
    }


@router.get("/{study_id}/voxel")
def get_voxel(
    study_id: int,
    x: int = Query(..., description="voxel column (x)"),
    y: int = Query(..., description="voxel row (y)"),
    z: int = Query(..., description="voxel slice (z)"),
    db: Session = Depends(get_db),
):
    """Inspect a single voxel: return HU and its physical world coordinate."""
    _validate_study(db, study_id)
    vol = _load_volume(study_id)
    data = vol["data"]
    depth, height, width = data.shape

    if not (0 <= x < width and 0 <= y < height and 0 <= z < depth):
        raise ValidationError("Voxel index out of volume bounds.", code="voxel_out_of_range")

    hu = float(data[z, y, x])

    cs = build_coordinate_system(
        tuple(float(v) for v in vol["spacing"]),
        tuple(float(v) for v in vol["origin"]),
        tuple(float(v) for v in vol["direction"]),
    )
    # voxel (x, y, z) → world; our CoordinateSystem.voxel_to_world expects
    # (ix, iy, iz) in column/row/slice order.
    world = cs.voxel_to_world((x, y, z))

    return {
        "index": [x, y, z],
        "world": list(world),
        "hu": hu,
    }
