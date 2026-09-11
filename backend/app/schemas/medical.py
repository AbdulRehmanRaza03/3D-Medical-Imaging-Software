"""Pydantic request/response schemas (typed API contracts)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --- Study ---
class SeriesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    series_uid: str
    series_number: int | None = None
    description: str | None = None
    modality: str | None = None
    rows: int | None = None
    columns: int | None = None
    slice_count: int
    pixel_spacing_x: float | None = None
    pixel_spacing_y: float | None = None
    slice_thickness: float | None = None
    slice_spacing: float | None = None
    image_orientation: str | None = None
    image_position: str | None = None
    is_selected: bool = False
    warnings: str | None = None


class StudyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    study_uid: str
    name: str
    modality: str | None = None
    status: str
    slice_count: int
    series_count: int
    study_date: str | None = None
    created_at: Any
    updated_at: Any
    error_message: str | None = None


class StudyListOut(BaseModel):
    studies: list[StudyOut]
    total: int


class StudyDetailOut(StudyOut):
    series: list[SeriesOut] = []


# --- Upload ---
class UploadResult(BaseModel):
    study: StudyOut
    series_detected: int
    warnings: list[str] = []


# --- Slice ---
class SliceMetaOut(BaseModel):
    index: int
    total: int
    instance_number: int | None = None
    slice_position: list[float] | None = None
    rows: int
    columns: int
    hu_min: float | None = None
    hu_max: float | None = None
    window_width: float | None = None
    window_level: float | None = None
    rescale_slope: float | None = None
    rescale_intercept: float | None = None


# --- Metadata ---
class MetadataOut(BaseModel):
    study_id: int
    study_uid: str
    patient_id: str | None = None
    modality: str | None = None
    study_date: str | None = None
    series_description: str | None = None
    rows: int | None = None
    columns: int | None = None
    slice_count: int
    pixel_spacing: list[float] | None = None
    slice_thickness: float | None = None
    slice_spacing: float | None = None
    image_orientation: list[float] | None = None
    image_position: list[float] | None = None
    rescale_slope: float | None = None
    rescale_intercept: float | None = None
    physical_size: list[float] | None = None
    warnings: list[str] = []


# --- Reconstruction ---
class ReconstructRequest(BaseModel):
    threshold_hu: float = Field(default=300.0, ge=-2000, le=4000)
    series_id: int | None = None
    method: Literal["marching_cubes"] = "marching_cubes"
    remove_small_components: bool = True
    min_component_fraction: float = Field(default=0.001, ge=0.0, le=1.0)
    smoothing_iterations: int = Field(default=0, ge=0, le=20)


class ReconstructResponse(BaseModel):
    job_id: str


class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    study_id: int
    series_id: int | None = None
    name: str
    method: str
    threshold_hu: float
    vertices: int
    triangles: int
    bbox_min: list[float] | None = None
    bbox_max: list[float] | None = None
    physical_size: list[float] | None = None
    status: str
    created_at: Any

    @model_validator(mode="before")
    @classmethod
    def _derive_lists(cls, obj: Any) -> Any:
        """Derive list-shaped fields from ORM scalar x/y/z columns."""
        if isinstance(obj, dict):
            return obj
        for prefix, target in ("bbox_min", "bbox_min"), ("bbox_max", "bbox_max"), ("physical_size", "physical_size"):
            vals = (
                getattr(obj, f"{prefix}_x", None),
                getattr(obj, f"{prefix}_y", None),
                getattr(obj, f"{prefix}_z", None),
            )
            if all(v is not None for v in vals):
                setattr(obj, target, [float(v) for v in vals])
        return obj


class ModelListOut(BaseModel):
    models: list[ModelOut]


# --- Measurements ---
class MeasurementRequest(BaseModel):
    points: list[list[float]] = Field(min_length=2)
    measurement_type: Literal["distance", "angle"] = "distance"


class MeasurementOut(BaseModel):
    id: int
    model_id: int
    measurement_type: str
    value: float
    unit: str
    points: list[list[float]]
    created_at: Any


class MeasurementResult(BaseModel):
    measurement: MeasurementOut


# --- Jobs ---
class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: int
    task_type: str
    status: str
    progress: float
    message: str | None = None
    error: str | None = None
    result_model_id: int | None = None
    created_at: Any
    updated_at: Any


# --- Common error ---
class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


# --- Dashboard ---
class DashboardStats(BaseModel):
    total_studies: int
    processed_studies: int
    models_generated: int
    recent_studies: list[StudyOut]
    processing_jobs: list[JobOut]
