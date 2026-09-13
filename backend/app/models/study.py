"""ORM models for the medical imaging pipeline.

Stores metadata and filesystem references only — never raw medical image
pixel data in database rows. Pixel data lives in the structured storage
directory under ``storage/studies/{study_id}/...``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StudyStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_uid: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255), default="Untitled Study")
    modality: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=StudyStatus.uploaded.value)
    slice_count: Mapped[int] = mapped_column(Integer, default=0)
    series_count: Mapped[int] = mapped_column(Integer, default=0)
    study_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    series: Mapped[list["Series"]] = relationship(
        back_populates="study", cascade="all, delete-orphan"
    )
    models: Mapped[list["MeshModel"]] = relationship(
        back_populates="study", cascade="all, delete-orphan"
    )


class Series(Base):
    __tablename__ = "series"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    series_uid: Mapped[str] = mapped_column(String(64), index=True)
    series_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    modality: Mapped[str | None] = mapped_column(String(16), nullable=True)
    rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    columns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    slice_count: Mapped[int] = mapped_column(Integer, default=0)
    pixel_spacing_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    pixel_spacing_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    slice_thickness: Mapped[float | None] = mapped_column(Float, nullable=True)
    slice_spacing: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_orientation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)

    study: Mapped["Study"] = relationship(back_populates="series")


class MeshModel(Base):
    __tablename__ = "mesh_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    series_id: Mapped[int | None] = mapped_column(
        ForeignKey("series.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), default="Bone Model")
    method: Mapped[str] = mapped_column(String(64), default="marching_cubes")
    threshold_hu: Mapped[float] = mapped_column(Float, default=300.0)
    vertices: Mapped[int] = mapped_column(Integer, default=0)
    triangles: Mapped[int] = mapped_column(Integer, default=0)
    bbox_min_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_min_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_min_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    physical_size_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    physical_size_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    physical_size_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    mesh_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="ready")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    study: Mapped["Study"] = relationship(back_populates="models")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    study_id: Mapped[int] = mapped_column(Integer, index=True)
    task_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default=JobStatus.queued.value)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_model_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("mesh_models.id", ondelete="CASCADE"), index=True
    )
    measurement_type: Mapped[str] = mapped_column(String(32))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16), default="mm")
    points: Mapped[str] = mapped_column(Text)  # JSON-encoded list of points
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class SegmentationResult(Base):
    """A stored AI segmentation result (mask + metadata).

    Only metadata and file references are stored here; the mask array lives in
    the structured storage directory under
    ``storage/studies/{study_id}/segmentations/``.
    """

    __tablename__ = "segmentation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    model_id: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(16), default="1.0")
    status: Mapped[str] = mapped_column(String(16), default="processing")
    mask_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Preserve the source geometry for alignment.
    spacing_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    spacing_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    spacing_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    origin_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    origin_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    origin_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    direction: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Label summary (JSON: list of label dicts with voxel_count/volume/bbox).
    labels: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    device: Mapped[str | None] = mapped_column(String(16), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
