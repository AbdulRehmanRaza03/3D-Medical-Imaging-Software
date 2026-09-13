"""Pydantic schemas for segmentation API contracts."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SegmentationModelInfo(BaseModel):
    """Metadata describing a registered segmentation model."""

    id: str
    name: str
    version: str
    task: str
    labels: list[str]
    framework: str
    target_spacing: list[float] | None = None
    checkpoint_path: str | None = None
    checkpoint_available: bool = False


class SegmentationJobRequest(BaseModel):
    model_id: str = "bone_1"
    study_id: int
    # Optional overrides.
    preprocessing: dict[str, Any] | None = None
    inference: dict[str, Any] | None = None
    post_processing: dict[str, Any] | None = None


class SegmentationJobResponse(BaseModel):
    job_id: str
    status: str


class SegmentationLabelOut(BaseModel):
    id: int
    name: str
    color: str
    voxel_count: int = 0
    volume_cm3: float = 0.0
    bbox_min: list[float] | None = None
    bbox_max: list[float] | None = None
    centroid: list[float] | None = None


class SegmentationResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    study_id: int
    model_id: str
    model_version: str
    status: str
    created_at: Any
    processing_duration_sec: float | None = None
    device: str | None = None
    labels: list[SegmentationLabelOut] = []
    error: str | None = None


class SegmentationResultListOut(BaseModel):
    results: list[SegmentationResultOut]


class SegmentationJobStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: int
    task_type: str
    status: str
    progress: float
    message: str | None = None
    error: str | None = None
    result_id: int | None = None
