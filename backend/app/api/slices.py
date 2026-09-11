"""API routes for 2D slice serving."""
from __future__ import annotations

import base64

import numpy as np
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.db.session import get_db
from app.models.study import Study
from app.schemas.medical import SliceMetaOut
from app.services import study_service, windowing_service

router = APIRouter(prefix="/studies", tags=["slices"])


@router.get("/{study_id}/slices", response_model=SliceMetaOut)
def slice_info(study_id: int, db: Session = Depends(get_db)) -> SliceMetaOut:
    """Return metadata and count for slice navigation."""
    study = db.get(Study, study_id)
    if study is None:
        raise NotFoundError("Study not found.", code="study_not_found")
    volume = _volume(study_id)
    depth = int(volume["data"].shape[0])
    hu = volume["data"]
    return SliceMetaOut(
        index=0,
        total=depth,
        rows=int(volume["data"].shape[1]),
        columns=int(volume["data"].shape[2]),
        hu_min=float(np.min(hu)),
        hu_max=float(np.max(hu)),
    )


@router.get("/{study_id}/slice/{index}")
def get_slice(
    study_id: int,
    index: int,
    width: float | None = None,
    level: float | None = None,
    db: Session = Depends(get_db),
):
    """Return a windowed 8-bit slice as a base64 PNG for canvas rendering."""
    study = db.get(Study, study_id)
    if study is None:
        raise NotFoundError("Study not found.", code="study_not_found")

    volume = _volume(study_id)
    depth = int(volume["data"].shape[0])
    if index < 0 or index >= depth:
        raise ValidationError(
            f"Slice index {index} out of range (0..{depth - 1}).",
            code="slice_out_of_range",
        )

    hu_slice = volume["data"][index]

    # Determine window/level.
    if width is None or level is None:
        hu_min = float(np.min(volume["data"]))
        hu_max = float(np.max(volume["data"]))
        width, level = windowing_service.default_window(hu_min, hu_max)

    display = windowing_service.apply_window(hu_slice, width, level)

    # Encode to PNG.
    from PIL import Image

    img = Image.fromarray(display, mode="L")
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")

    return JSONResponse(
        content={
            "index": index,
            "total": depth,
            "width": width,
            "level": level,
            "rows": int(display.shape[0]),
            "columns": int(display.shape[1]),
            "image_base64": encoded,
        }
    )


def _volume(study_id: int):
    return study_service.load_volume(study_id)
