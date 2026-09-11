"""Lightweight background processing-job system.

Phase 1 uses a simple thread-pool executor. The interface is deliberately
decoupled so a Redis/Celery (or other) backend can be swapped in later without
changing the API contract. Job state is persisted to the database and polled by
the frontend.
"""
from __future__ import annotations

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import SessionLocal
from app.models.study import JobStatus, ProcessingJob, Study, StudyStatus, MeshModel
from app.schemas.medical import ReconstructRequest

logger = logging.getLogger(__name__)

# A modest worker pool for CPU-bound reconstruction on a laptop.
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ov-worker")

_progress_hooks: dict[str, Callable[[float, str], None]] = {}


def _create_job(db: Session, study_id: int, task_type: str) -> ProcessingJob:
    job = ProcessingJob(
        id=str(uuid.uuid4()),
        study_id=study_id,
        task_type=task_type,
        status=JobStatus.queued.value,
        progress=0.0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _update_job(
    job_id: str,
    *,
    status: str | None = None,
    progress: float | None = None,
    message: str | None = None,
    error: str | None = None,
    result_model_id: int | None = None,
) -> None:
    db = SessionLocal()
    try:
        job = db.get(ProcessingJob, job_id)
        if job is None:
            return
        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if message is not None:
            job.message = message
        if error is not None:
            job.error = error
        if result_model_id is not None:
            job.result_model_id = result_model_id
        db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("Failed to update job %s", job_id)
    finally:
        db.close()


def get_job(db: Session, job_id: str) -> ProcessingJob:
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise NotFoundError("Job not found.", code="job_not_found")
    return job


def submit_reconstruction(
    db: Session,
    study_id: int,
    req: ReconstructRequest,
) -> ProcessingJob:
    """Queue a reconstruction job and return its job ID immediately."""
    study = db.get(Study, study_id)
    if study is None:
        raise NotFoundError("Study not found.", code="study_not_found")

    job = _create_job(db, study_id, "reconstruction")
    study.status = StudyStatus.processing.value
    db.commit()

    _executor.submit(
        _run_reconstruction,
        job.id,
        study_id,
        req,
    )
    return job


def _run_reconstruction(job_id: str, study_id: int, req: ReconstructRequest) -> None:
    from app.services import reconstruction_service, study_service
    from app.services.storage import storage_service

    try:
        _update_job(job_id, status=JobStatus.processing.value, progress=0.05,
                     message="Loading volume…")

        loaded = study_service.load_volume(study_id)
        data = loaded["data"]
        from app.services.volume_service import Volume

        volume = Volume(
            data=data,
            spacing=tuple(float(v) for v in loaded["spacing"]),
            origin=tuple(float(v) for v in loaded["origin"]),
            direction=tuple(float(v) for v in loaded["direction"]),
            dimensions=tuple(int(v) for v in loaded["dimensions"]),
        )

        _update_job(job_id, progress=0.25, message="Thresholding…")
        mesh = reconstruction_service.reconstruct_bone(
            volume,
            threshold_hu=req.threshold_hu,
            remove_small_components=req.remove_small_components,
            min_component_fraction=req.min_component_fraction,
            smoothing_iterations=req.smoothing_iterations,
        )

        _update_job(job_id, progress=0.75, message="Saving mesh…")
        mesh_path = storage_service.save_model_mesh(
            study_id, mesh.vertices, mesh.faces
        )

        db = SessionLocal()
        try:
            model = MeshModel(
                study_id=study_id,
                series_id=_selected_series_id(db, study_id),
                name=f"Bone @ {int(req.threshold_hu)} HU",
                method=req.method,
                threshold_hu=req.threshold_hu,
                vertices=int(mesh.vertices.shape[0]),
                triangles=int(mesh.faces.shape[0]),
                bbox_min_x=mesh.bbox_min[0],
                bbox_min_y=mesh.bbox_min[1],
                bbox_min_z=mesh.bbox_min[2],
                bbox_max_x=mesh.bbox_max[0],
                bbox_max_y=mesh.bbox_max[1],
                bbox_max_z=mesh.bbox_max[2],
                physical_size_x=mesh.physical_size[0],
                physical_size_y=mesh.physical_size[1],
                physical_size_z=mesh.physical_size[2],
                mesh_path=str(mesh_path),
                status="ready",
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            model_id = model.id

            study = db.get(Study, study_id)
            if study:
                study.status = StudyStatus.ready.value
                db.commit()

            _update_job(
                job_id,
                status=JobStatus.completed.value,
                progress=1.0,
                message="Reconstruction complete.",
                result_model_id=model_id,
            )
        finally:
            db.close()

    except Exception as exc:  # noqa: BLE001
        logger.exception("Reconstruction job %s failed", job_id)
        _update_job(job_id, status=JobStatus.failed.value, progress=1.0,
                     error=str(exc), message="Reconstruction failed.")
        db = SessionLocal()
        try:
            study = db.get(Study, study_id)
            if study and study.status != StudyStatus.ready.value:
                study.status = StudyStatus.failed.value
                study.error_message = str(exc)
                db.commit()
        finally:
            db.close()


def _selected_series_id(db: Session, study_id: int) -> int | None:
    from sqlalchemy import select

    from app.models.study import Series

    row = db.execute(
        select(Series.id).where(Series.study_id == study_id, Series.is_selected.is_(True))
    ).first()
    return row[0] if row else None
