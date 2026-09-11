"""API routes for jobs and dashboard stats."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.study import MeshModel, ProcessingJob, Study, StudyStatus
from app.schemas.medical import DashboardStats, JobOut, StudyOut
from app.services import job_service

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    job = job_service.get_job(db, job_id)
    return JobOut.model_validate(job)


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)) -> DashboardStats:
    total_studies = db.execute(select(func.count(Study.id))).scalar_one()
    processed_studies = db.execute(
        select(func.count(Study.id)).where(Study.status == StudyStatus.ready.value)
    ).scalar_one()
    models_generated = db.execute(select(func.count(MeshModel.id))).scalar_one()

    recent = db.execute(
        select(Study).order_by(Study.created_at.desc()).limit(10)
    ).scalars().all()

    active_jobs = db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.status.in_(["queued", "processing"]))
        .order_by(ProcessingJob.created_at.desc())
        .limit(10)
    ).scalars().all()

    return DashboardStats(
        total_studies=total_studies,
        processed_studies=processed_studies,
        models_generated=models_generated,
        recent_studies=[StudyOut.model_validate(s) for s in recent],
        processing_jobs=[JobOut.model_validate(j) for j in active_jobs],
    )
