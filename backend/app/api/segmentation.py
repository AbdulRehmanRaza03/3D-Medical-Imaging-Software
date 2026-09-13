"""Segmentation API endpoints (Phase 3).

Exposes model listing, job submission, job status, result retrieval, and
result deletion. Uses the existing job system; no AI results are fabricated.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.segmentation import registry
from ai.segmentation.schemas import (
    SegmentationJobRequest,
    SegmentationJobResponse,
    SegmentationJobStatusOut,
    SegmentationModelInfo,
    SegmentationResultListOut,
    SegmentationResultOut,
)
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.study import SegmentationResult, Study
from app.services import job_service

router = APIRouter(tags=["segmentation"])


@router.get("/segmentation/models", response_model=list[SegmentationModelInfo])
def list_segmentation_models():
    """List registered segmentation models and their checkpoint availability."""
    return [SegmentationModelInfo(**m) for m in registry.list_models()]


@router.post("/segmentation/jobs", response_model=SegmentationJobResponse)
def create_segmentation_job(
    req: SegmentationJobRequest,
    db: Session = Depends(get_db),
) -> SegmentationJobResponse:
    study = db.get(Study, req.study_id)
    if study is None:
        raise NotFoundError("Study not found.", code="study_not_found")

    job = job_service.submit_segmentation(db, req.study_id, req.model_id)
    return SegmentationJobResponse(job_id=job.id, status=job.status)


@router.get("/segmentation/jobs/{job_id}", response_model=SegmentationJobStatusOut)
def get_segmentation_job(job_id: str, db: Session = Depends(get_db)) -> SegmentationJobStatusOut:
    job = job_service.get_job(db, job_id)
    return SegmentationJobStatusOut.model_validate(job)


@router.get("/studies/{study_id}/segmentations", response_model=SegmentationResultListOut)
def list_segmentations(study_id: int, db: Session = Depends(get_db)) -> SegmentationResultListOut:
    results = db.execute(
        select(SegmentationResult)
        .where(SegmentationResult.study_id == study_id)
        .order_by(SegmentationResult.created_at.desc())
    ).scalars().all()
    return SegmentationResultListOut(
        results=[_to_out(r) for r in results]
    )


@router.get("/segmentation/results/{result_id}", response_model=SegmentationResultOut)
def get_segmentation_result(result_id: int, db: Session = Depends(get_db)) -> SegmentationResultOut:
    result = db.get(SegmentationResult, result_id)
    if result is None:
        raise NotFoundError("Segmentation result not found.", code="result_not_found")
    return _to_out(result)


@router.delete("/segmentation/results/{result_id}", status_code=204)
def delete_segmentation_result(result_id: int, db: Session = Depends(get_db)):
    result = db.get(SegmentationResult, result_id)
    if result is None:
        raise NotFoundError("Segmentation result not found.", code="result_not_found")
    db.delete(result)
    db.commit()


def _to_out(r: SegmentationResult) -> SegmentationResultOut:
    labels = []
    if r.labels:
        try:
            labels = json.loads(r.labels)
        except (json.JSONDecodeError, TypeError):
            labels = []
    return SegmentationResultOut(
        id=r.id,
        study_id=r.study_id,
        model_id=r.model_id,
        model_version=r.model_version,
        status=r.status,
        created_at=r.created_at,
        processing_duration_sec=r.processing_duration_sec,
        device=r.device,
        labels=labels,
        error=r.error,
    )
