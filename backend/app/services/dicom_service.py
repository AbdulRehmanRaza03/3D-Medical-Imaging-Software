"""DICOM ingestion: validation, series detection, slice ordering, metadata.

This module is deliberately pure with respect to web/IO concerns — it takes
``pydicom.Dataset`` objects and returns plain Python data structures so it can
be unit-tested without a running server.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pydicom
from pydicom import dcmread

from app.core.exceptions import InvalidDicomError, NoCompatibleSeriesError

# Tags that must be present for a minimally usable CT image instance.
REQUIRED_TAGS = [
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "SOPInstanceUID",
    "Modality",
    "Rows",
    "Columns",
    "PixelData",
    "ImagePositionPatient",
    "ImageOrientationPatient",
    "PixelSpacing",
]

CT_MODALITY = "CT"


@dataclass
class SliceInfo:
    """Processed, orderable representation of a single 2D CT slice."""

    sop_instance_uid: str
    instance_number: int | None
    image_position: tuple[float, float, float] | None
    sort_key: float
    dataset: pydicom.Dataset


@dataclass
class SeriesInfo:
    """A detected DICOM series belonging to a study."""

    series_uid: str
    series_number: int | None = None
    description: str | None = None
    modality: str | None = None
    rows: int | None = None
    columns: int | None = None
    pixel_spacing: tuple[float, float] | None = None
    slice_thickness: float | None = None
    slice_spacing: float | None = None
    image_orientation: tuple[float, ...] | None = None
    image_position: tuple[float, ...] | None = None
    rescale_slope: float | None = None
    rescale_intercept: float | None = None
    window_width: float | None = None
    window_level: float | None = None
    slices: list[SliceInfo] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def slice_count(self) -> int:
        return len(self.slices)


@dataclass
class StudyResult:
    """Result of ingesting a set of DICOM files for one study."""

    study_uid: str
    patient_id: str | None
    study_date: str | None
    modality: str | None
    series: list[SeriesInfo]
    warnings: list[str] = field(default_factory=list)


def _safe_tag(ds: pydicom.Dataset, name: str) -> Any:
    """Return a tag value or ``None``, swallowing missing/invalid tags."""
    try:
        value = getattr(ds, name)
        if value is None:
            return None
        return value
    except Exception:
        return None


def _as_float_tuple(value: Any) -> tuple[float, ...] | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        try:
            return tuple(float(v) for v in value)
        except (TypeError, ValueError):
            return None
    if isinstance(value, pydicom.multival.MultiValue):
        try:
            return tuple(float(v) for v in value)
        except (TypeError, ValueError):
            return None
    return None


def validate_dicom_dataset(ds: pydicom.Dataset) -> list[str]:
    """Validate a single DICOM dataset, returning a list of problems."""
    problems: list[str] = []
    for tag in REQUIRED_TAGS:
        if _safe_tag(ds, tag) is None:
            problems.append(f"Missing required tag: {tag}")
    return problems


def read_dicom_bytes(data: bytes) -> pydicom.Dataset:
    """Parse DICOM from raw bytes, raising a friendly error on failure."""
    try:
        return dcmread(io.BytesIO(data), force=False)
    except Exception as exc:  # noqa: BLE001 - convert to friendly error
        raise InvalidDicomError(
            "The uploaded file is not a valid DICOM dataset.",
            code="invalid_dicom",
        ) from exc


def is_ct(ds: pydicom.Dataset) -> bool:
    return _safe_tag(ds, "Modality") == CT_MODALITY


def _has_image_data(ds: pydicom.Dataset) -> bool:
    return _safe_tag(ds, "PixelData") is not None


def compute_slice_sort_key(ds: pydicom.Dataset) -> tuple[float, ...]:
    """Compute a spatial sort key based on ImagePositionPatient orientation.

    Sorting DICOM slices by filename is incorrect for anatomically accurate
    3D volumes. We project ``ImagePositionPatient`` onto the slice-normal axis
    derived from ``ImageOrientationPatient``, which gives the true anatomical
    ordering regardless of acquisition order or filename conventions.
    """
    position = _as_float_tuple(_safe_tag(ds, "ImagePositionPatient"))
    orientation = _as_float_tuple(_safe_tag(ds, "ImageOrientationPatient"))

    if position and orientation and len(orientation) >= 6:
        # Row and column direction cosines.
        row_cos = np.array(orientation[0:3], dtype=float)
        col_cos = np.array(orientation[3:6], dtype=float)
        # Slice normal = cross(row, col).
        normal = np.cross(row_cos, col_cos)
        norm = np.linalg.norm(normal)
        if norm > 0:
            normal = normal / norm
            position_arr = np.array(position, dtype=float)
            return (float(np.dot(position_arr, normal)),)
        return (float(position[2]),)

    # Fallbacks, in decreasing order of reliability.
    if position:
        return (float(position[2]),)
    instance = _safe_tag(ds, "InstanceNumber")
    if instance is not None:
        try:
            return (float(instance),)
        except (TypeError, ValueError):
            pass
    sop = _safe_tag(ds, "SOPInstanceUID")
    return (float(sop) if sop and not isinstance(sop, str) else 0.0,)


def _compute_slice_spacing(slices: list[SliceInfo]) -> float | None:
    """Estimate slice spacing from sorted ImagePositionPatient values."""
    keys = [s.sort_key for s in slices]
    if len(keys) < 2:
        return None
    diffs = np.diff(np.array(keys, dtype=float))
    diffs = np.abs(diffs[diffs != 0])
    if diffs.size == 0:
        return None
    return float(np.median(diffs))


def detect_series(datasets: list[pydicom.Dataset]) -> StudyResult:
    """Group DICOM datasets into a study and detect CT series.

    Raises ``InvalidDicomError`` if nothing is a valid DICOM, and
    ``NoCompatibleSeriesError`` if no usable CT series exists.
    """
    if not datasets:
        raise InvalidDicomError(
            "No files were provided to process.", code="no_files"
        )

    groups: dict[str, list[pydicom.Dataset]] = {}
    study_uid: str | None = None
    patient_id: str | None = None
    study_date: str | None = None
    modality: str | None = None

    for ds in datasets:
        suid = _safe_tag(ds, "StudyInstanceUID")
        if study_uid is None:
            study_uid = str(suid)
        if patient_id is None:
            patient_id = _safe_tag(ds, "PatientID")
        if study_date is None:
            study_date = _safe_tag(ds, "StudyDate")
        if modality is None:
            modality = _safe_tag(ds, "Modality")

        sruid = _safe_tag(ds, "SeriesInstanceUID")
        if sruid is None:
            continue
        groups.setdefault(str(sruid), []).append(ds)

    if study_uid is None:
        raise InvalidDicomError(
            "Uploaded files do not contain a valid DICOM study.",
            code="invalid_study",
        )

    series_list: list[SeriesInfo] = []
    warnings: list[str] = []

    for sruid, sds_list in groups.items():
        # Only consider series that have image instances.
        image_ds = [d for d in sds_list if _has_image_data(d)]
        if not image_ds:
            continue

        ref = image_ds[0]
        if not is_ct(ref):
            continue

        series = SeriesInfo(
            series_uid=sruid,
            series_number=(
                int(ref.SeriesNumber) if _safe_tag(ref, "SeriesNumber") is not None else None
            ),
            description=_safe_tag(ref, "SeriesDescription"),
            modality=CT_MODALITY,
            rows=_safe_tag(ref, "Rows"),
            columns=_safe_tag(ref, "Columns"),
            pixel_spacing=_as_float_tuple(_safe_tag(ref, "PixelSpacing"))[:2],
            slice_thickness=(
                float(ref.SliceThickness)
                if _safe_tag(ref, "SliceThickness") is not None
                else None
            ),
            image_orientation=_as_float_tuple(_safe_tag(ref, "ImageOrientationPatient")),
            image_position=_as_float_tuple(_safe_tag(ref, "ImagePositionPatient")),
            rescale_slope=(
                float(ref.RescaleSlope) if _safe_tag(ref, "RescaleSlope") is not None else 1.0
            ),
            rescale_intercept=(
                float(ref.RescaleIntercept)
                if _safe_tag(ref, "RescaleIntercept") is not None
                else 0.0
            ),
            window_width=(
                float(ref.WindowWidth)
                if _safe_tag(ref, "WindowWidth") is not None
                else None
            ),
            window_level=(
                float(ref.WindowCenter)
                if _safe_tag(ref, "WindowCenter") is not None
                else None
            ),
        )

        # Build slice infos and sort anatomically.
        for ds in image_ds:
            series.slices.append(
                SliceInfo(
                    sop_instance_uid=str(_safe_tag(ds, "SOPInstanceUID")),
                    instance_number=(
                        int(ds.InstanceNumber)
                        if _safe_tag(ds, "InstanceNumber") is not None
                        and str(_safe_tag(ds, "InstanceNumber")).lstrip("-").isdigit()
                        else None
                    ),
                    image_position=_as_float_tuple(_safe_tag(ds, "ImagePositionPatient")),
                    sort_key=compute_slice_sort_key(ds)[0],
                    dataset=ds,
                )
            )

        series.slices.sort(key=lambda s: (s.sort_key, s.instance_number or 0))

        # Warnings for irregular/missing/duplicate slices.
        _warn_series_quality(series)
        warnings.extend(series.warnings)

        series_list.append(series)

    if not series_list:
        raise NoCompatibleSeriesError(
            "No compatible CT series was found in the uploaded study.",
            code="no_compatible_series",
        )

    # Order series by series number for stable presentation.
    series_list.sort(key=lambda s: (s.series_number is None, s.series_number or 0))

    return StudyResult(
        study_uid=study_uid,
        patient_id=patient_id,
        study_date=_to_date_str(study_date),
        modality=CT_MODALITY,
        series=series_list,
        warnings=warnings,
    )


def _to_date_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _warn_series_quality(series: SeriesInfo) -> None:
    """Attach useful warnings about slice ordering/spacing issues."""
    if series.slice_count < 2:
        series.warnings.append(
            "Series contains fewer than 2 slices; 3D reconstruction will be limited."
        )

    # Detect duplicate sort keys (duplicate slices).
    keys = [s.sort_key for s in series.slices]
    unique = set(keys)
    if len(unique) < len(keys):
        series.warnings.append(
            f"Series contains {len(keys) - len(unique)} duplicated slice position(s)."
        )

    # Detect irregular spacing.
    if len(keys) >= 3:
        diffs = np.abs(np.diff(np.array(keys, dtype=float)))
        diffs = diffs[diffs != 0]
        if diffs.size > 0:
            med = np.median(diffs)
            if med > 0:
                rel = diffs / med
                if np.max(rel) > 1.5:
                    series.warnings.append(
                        "Irregular slice spacing detected; volume may be "
                        "geometrically inconsistent."
                    )

    # Validate orientation is roughly axial.
    orient = series.image_orientation
    if orient and len(orient) >= 6:
        row_cos = np.array(orient[0:3], dtype=float)
        col_cos = np.array(orient[3:6], dtype=float)
        normal = np.cross(row_cos, col_cos)
        norm = np.linalg.norm(normal)
        if norm > 0:
            normal = normal / norm
            # Axial slice normal should be close to (0,0,±1).
            axial_score = abs(normal[2])
            if axial_score < 0.7:
                series.warnings.append(
                    "Series orientation is not near-axial; 3D rendering "
                    "orientation may differ from anatomical convention."
                )
