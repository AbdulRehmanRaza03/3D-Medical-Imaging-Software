"""API routes for study ingestion and metadata."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.study import Series, Study
from app.schemas.medical import (
    MetadataOut,
    SeriesOut,
    StudyDetailOut,
    StudyListOut,
    StudyOut,
    UploadResult,
)
from app.services import study_service

router = APIRouter(prefix="/studies", tags=["studies"])


@router.post("/upload", response_model=UploadResult, status_code=201)
async def upload_study(
    files: list[UploadFile] = File(...),
    name: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> UploadResult:
    """Upload and ingest a DICOM CT study.

    Accepts multiple DICOM files. Files are validated, series detected, slices
    ordered, metadata extracted, and a 3D volume constructed.
    """
    raw_files: list[tuple[str, bytes]] = []
    for uf in files:
        data = await uf.read()
        raw_files.append((uf.filename or "unnamed", data))

    study, warnings = study_service.ingest_study(db, raw_files, name=name)
    return UploadResult(
        study=StudyOut.model_validate(study),
        series_detected=study.series_count,
        warnings=warnings,
    )


@router.get("", response_model=StudyListOut)
def list_studies(db: Session = Depends(get_db)) -> StudyListOut:
    studies = db.execute(select(Study).order_by(Study.created_at.desc())).scalars().all()
    return StudyListOut(
        studies=[StudyOut.model_validate(s) for s in studies],
        total=len(studies),
    )


@router.get("/{study_id}", response_model=StudyDetailOut)
def get_study(study_id: int, db: Session = Depends(get_db)) -> StudyDetailOut:
    study = db.get(Study, study_id)
    if study is None:
        raise NotFoundError("Study not found.", code="study_not_found")
    detail = StudyDetailOut.model_validate(study)
    detail.series = [SeriesOut.model_validate(s) for s in study.series]
    return detail


@router.get("/{study_id}/series", response_model=list[SeriesOut])
def list_series(study_id: int, db: Session = Depends(get_db)) -> list[SeriesOut]:
    series = db.execute(
        select(Series).where(Series.study_id == study_id).order_by(Series.series_number)
    ).scalars().all()
    return [SeriesOut.model_validate(s) for s in series]


@router.get("/{study_id}/metadata", response_model=MetadataOut)
def get_metadata(study_id: int, db: Session = Depends(get_db)) -> MetadataOut:
    study = db.get(Study, study_id)
    if study is None:
        raise NotFoundError("Study not found.", code="study_not_found")

    series = db.execute(
        select(Series)
        .where(Series.study_id == study_id, Series.is_selected.is_(True))
    ).scalars().first()

    if series is None:
        series = db.execute(
            select(Series).where(Series.study_id == study_id)
        ).scalars().first()

    volume = study_service.load_volume(study_id)

    return MetadataOut(
        study_id=study.id,
        study_uid=study.study_uid,
        patient_id=None,  # PHI intentionally not surfaced
        modality=study.modality,
        study_date=study.study_date,
        series_description=series.description if series else None,
        rows=series.rows if series else None,
        columns=series.columns if series else None,
        slice_count=study.slice_count,
        pixel_spacing=_spacing(series),
        slice_thickness=series.slice_thickness if series else None,
        slice_spacing=series.slice_spacing if series else None,
        image_orientation=_to_list(series.image_orientation) if series else None,
        image_position=_to_list(series.image_position) if series else None,
        rescale_slope=None,
        rescale_intercept=None,
        physical_size=_physical_size(volume),
        warnings=_warnings(series),
    )


def _spacing(series: Series | None) -> list[float] | None:
    if series is None:
        return None
    if series.pixel_spacing_x is None or series.pixel_spacing_y is None:
        return None
    return [series.pixel_spacing_x, series.pixel_spacing_y]


def _to_list(value: str | None) -> list[float] | None:
    if not value:
        return None
    try:
        return [float(v) for v in value.split(",")]
    except (ValueError, TypeError):
        return None


def _physical_size(volume: Any) -> list[float] | None:
    if volume is None:
        return None
    try:
        dims = [float(v) for v in volume["dimensions"]]
        spacing = [float(v) for v in volume["spacing"]]
        return [
            dims[0] * spacing[0],
            dims[1] * spacing[1],
            dims[2] * spacing[2],
        ]
    except (KeyError, IndexError, TypeError):
        return None


def _warnings(series: Series | None) -> list[str]:
    if series is None or not series.warnings:
        return []
    return [w.strip() for w in series.warnings.split(";") if w.strip()]
