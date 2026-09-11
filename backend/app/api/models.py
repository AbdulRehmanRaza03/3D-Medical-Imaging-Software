"""API routes for reconstruction, models, measurements, and export."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ProcessingError, ValidationError
from app.db.session import get_db
from app.models.study import Measurement, MeshModel, Study
from app.schemas.medical import (
    MeasurementOut,
    MeasurementRequest,
    MeasurementResult,
    ModelListOut,
    ModelOut,
    ReconstructRequest,
    ReconstructResponse,
)
from app.services import (
    export_service,
    job_service,
    measurement_service,
    reconstruction_service,
)
from app.services.storage import storage_service
from app.services.reconstruction_service import MeshData

router = APIRouter(tags=["models"])


@router.post("/studies/{study_id}/reconstruct", response_model=ReconstructResponse)
def reconstruct(
    study_id: int,
    req: ReconstructRequest,
    db: Session = Depends(get_db),
) -> ReconstructResponse:
    study = db.get(Study, study_id)
    if study is None:
        raise NotFoundError("Study not found.", code="study_not_found")
    job = job_service.submit_reconstruction(db, study_id, req)
    return ReconstructResponse(job_id=job.id)


@router.get("/studies/{study_id}/models", response_model=ModelListOut)
def list_models(study_id: int, db: Session = Depends(get_db)) -> ModelListOut:
    study = db.get(Study, study_id)
    if study is None:
        raise NotFoundError("Study not found.", code="study_not_found")
    models = db.execute(
        select(MeshModel).where(MeshModel.study_id == study_id).order_by(MeshModel.created_at.desc())
    ).scalars().all()
    return ModelListOut(models=[ModelOut.model_validate(m) for m in models])


@router.get("/models/{model_id}", response_model=ModelOut)
def get_model(model_id: int, db: Session = Depends(get_db)) -> ModelOut:
    model = db.get(MeshModel, model_id)
    if model is None:
        raise NotFoundError("Model not found.", code="model_not_found")
    return ModelOut.model_validate(model)


@router.get("/models/{model_id}/mesh")
def get_mesh(model_id: int, db: Session = Depends(get_db)):
    """Return the model mesh (vertices/faces) as binary GLB for the 3D viewer.

    Binary transport avoids the huge JSON overhead of large meshes.
    """
    model = db.get(MeshModel, model_id)
    if model is None:
        raise NotFoundError("Model not found.", code="model_not_found")

    mesh = _load_mesh(model)
    glb = export_service.export_glb(mesh)
    return Response(
        content=glb,
        media_type="model/gltf-binary",
        headers={"Content-Disposition": f'inline; filename="model_{model_id}.glb"'},
    )


@router.post("/models/{model_id}/measurements", response_model=MeasurementResult)
def create_measurement(
    model_id: int,
    req: MeasurementRequest,
    db: Session = Depends(get_db),
) -> MeasurementResult:
    model = db.get(MeshModel, model_id)
    if model is None:
        raise NotFoundError("Model not found.", code="model_not_found")

    if req.measurement_type == "distance":
        if len(req.points) != 2:
            raise ValidationError("Distance requires exactly 2 points.", code="bad_points")
        value = measurement_service.distance_mm(req.points[0], req.points[1])
        unit = "mm"
    elif req.measurement_type == "angle":
        if len(req.points) != 3:
            raise ValidationError("Angle requires exactly 3 points.", code="bad_points")
        value = measurement_service.angle_deg(req.points[0], req.points[1], req.points[2])
        unit = "deg"
    else:
        raise ValidationError("Unsupported measurement type.", code="bad_type")

    measurement = Measurement(
        model_id=model_id,
        measurement_type=req.measurement_type,
        value=value,
        unit=unit,
        points=json.dumps(req.points),
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)

    return MeasurementResult(
        measurement=MeasurementOut(
            id=measurement.id,
            model_id=measurement.model_id,
            measurement_type=measurement.measurement_type,
            value=measurement.value,
            unit=measurement.unit,
            points=json.loads(measurement.points),
            created_at=measurement.created_at,
        )
    )


@router.get("/models/{model_id}/export/{fmt}")
def export_model(
    model_id: int,
    fmt: str,
    db: Session = Depends(get_db),
) -> Response:
    model = db.get(MeshModel, model_id)
    if model is None:
        raise NotFoundError("Model not found.", code="model_not_found")

    if fmt not in {"stl", "obj", "glb"}:
        raise ValidationError(f"Unsupported format: {fmt}", code="bad_format")

    mesh = _load_mesh(model)
    data = export_service.export_mesh(mesh, fmt)

    media_types = {
        "stl": "model/stl",
        "obj": "text/plain",
        "glb": "model/gltf-binary",
    }
    return Response(
        content=data,
        media_type=media_types[fmt],
        headers={
            "Content-Disposition": f'attachment; filename="model_{model_id}.{fmt}"'
        },
    )


def _load_mesh(model: MeshModel) -> MeshData:
    verts, faces = storage_service.load_model_mesh(model.mesh_path)
    return MeshData(
        vertices=verts,
        faces=faces,
        bbox_min=_bbox_min(model),
        bbox_max=_bbox_max(model),
        physical_size=_physical(model),
        threshold_hu=model.threshold_hu,
    )


def _bbox_min(model: MeshModel):
    return (
        model.bbox_min_x or 0.0,
        model.bbox_min_y or 0.0,
        model.bbox_min_z or 0.0,
    )


def _bbox_max(model: MeshModel):
    return (
        model.bbox_max_x or 0.0,
        model.bbox_max_y or 0.0,
        model.bbox_max_z or 0.0,
    )


def _physical(model: MeshModel):
    return (
        model.physical_size_x or 0.0,
        model.physical_size_y or 0.0,
        model.physical_size_z or 0.0,
    )
