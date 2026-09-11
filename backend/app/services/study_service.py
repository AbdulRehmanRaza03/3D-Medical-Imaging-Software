"""High-level study orchestration: upload, ingestion, volume construction.

This service wires the medical pipeline together and persists metadata to the
database while storing binary artifacts on disk.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
from pydicom import dcmread
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidDicomError, NotFoundError
from app.models.study import (
    JobStatus,
    MeshModel,
    ProcessingJob,
    Series,
    Study,
    StudyStatus,
)
from app.services import dicom_service, volume_service
from app.services.dicom_service import SliceInfo, SeriesInfo, StudyResult
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


def _persist_study(db: Session, result: StudyResult, name: str | None) -> Study:
    study = Study(
        study_uid=result.study_uid,
        name=name or "Untitled Study",
        modality=result.modality,
        status=StudyStatus.processing.value,
        slice_count=sum(s.slice_count for s in result.series),
        series_count=len(result.series),
        study_date=result.study_date,
    )
    db.add(study)
    db.flush()

    for series_info in result.series:
        series = Series(
            study_id=study.id,
            series_uid=series_info.series_uid,
            series_number=series_info.series_number,
            description=series_info.description,
            modality=series_info.modality,
            rows=series_info.rows,
            columns=series_info.columns,
            slice_count=series_info.slice_count,
            pixel_spacing_x=(
                series_info.pixel_spacing[0]
                if series_info.pixel_spacing and len(series_info.pixel_spacing) >= 1
                else None
            ),
            pixel_spacing_y=(
                series_info.pixel_spacing[1]
                if series_info.pixel_spacing and len(series_info.pixel_spacing) >= 2
                else None
            ),
            slice_thickness=series_info.slice_thickness,
            slice_spacing=(
                dicom_service._compute_slice_spacing(series_info.slices)
            ),
            image_orientation=_fmt(series_info.image_orientation),
            image_position=_fmt(series_info.image_position),
            is_selected=False,
            warnings=_join(series_info.warnings),
        )
        db.add(series)
    db.flush()

    return study


def _fmt(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return ",".join(str(v) for v in value)
    return str(value)


def _join(values: list[str]) -> str | None:
    if not values:
        return None
    return "; ".join(values)


def ingest_study(
    db: Session,
    files: list[tuple[str, bytes]],
    name: str | None = None,
) -> tuple[Study, list[str]]:
    """Validate, detect series, build volume, and persist a study.

    Returns ``(study, warnings)``. Raises on invalid/no-CT input.
    """
    if not files:
        raise InvalidDicomError("No files were uploaded.", code="no_files")

    # Parse all files to datasets first (so we can validate overall input).
    datasets = []
    for _fname, data in files:
        try:
            datasets.append(dcmread(_to_bytesio(data), force=False))
        except Exception as exc:  # noqa: BLE001
            raise InvalidDicomError(
                "One or more uploaded files are not valid DICOM datasets.",
                code="invalid_dicom",
            ) from exc

    if not datasets:
        raise InvalidDicomError("No valid DICOM datasets found.", code="invalid_dicom")

    result = dicom_service.detect_series(datasets)

    # Persist study + series metadata.
    study = _persist_study(db, result, name)

    # Save DICOM files to disk.
    storage_service.save_dicom_files(study.id, files)

    # Select the primary series (first CT series) and build a volume.
    selected = result.series[0]
    _select_series(db, study.id, selected.series_uid)
    _build_and_store_volume(study.id, selected)

    # Mark study ready.
    study.status = StudyStatus.ready.value
    db.commit()
    db.refresh(study)

    return study, result.warnings


def _to_bytesio(data: bytes):
    import io

    return io.BytesIO(data)


def _select_series(db: Session, study_id: int, series_uid: str) -> None:
    series = db.execute(
        select(Series).where(
            Series.study_id == study_id, Series.series_uid == series_uid
        )
    ).scalar_one()
    series.is_selected = True


def _build_and_store_volume(study_id: int, series_info: SeriesInfo) -> None:
    volume = volume_service.build_volume(series_info)
    data = volume.data
    meta = {
        "spacing": list(volume.spacing),
        "origin": list(volume.origin),
        "direction": list(volume.direction),
        "dimensions": list(volume.dimensions),
    }
    # Store volume + metadata together.
    buf = _encode_volume(data, meta)
    storage_service.save_volume(study_id, buf, "volume.npz")


def _encode_volume(data: np.ndarray, meta: dict) -> bytes:
    import io

    import numpy as np

    buf = io.BytesIO()
    np.savez_compressed(buf, data=data, **{k: np.array(v) for k, v in meta.items()})
    return buf.getvalue()


def load_volume(study_id: int):
    """Load a saved volume's data + metadata for a study."""
    import io

    from app.services.storage.storage_service import volume_dir

    vdir = volume_dir(study_id)
    candidates = list(vdir.glob("*.npz"))
    if not candidates:
        raise NotFoundError("Volume not found for study.", code="volume_missing")
    path = candidates[0]
    loaded = np.load(path, allow_pickle=False)
    return loaded
