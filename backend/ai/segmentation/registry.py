"""Segmentation model registry.

Keeps the mapping from model IDs to their metadata and checkpoint locations.
New models (femur, pelvis, hip, ...) can be registered here without changing
the inference pipeline. Only models with an available checkpoint are reported
as runnable; the rest are listed but disabled.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RegisteredModel:
    id: str
    name: str
    version: str
    task: str
    labels: tuple[str, ...]
    framework: str
    target_spacing: tuple[float, float, float] | None
    checkpoint_filename: str | None  # relative to models dir; None = no weights yet
    architecture: str = "unet3d"  # unet3d | segresnet | unetr | ...


def _models_dir() -> str:
    # Models directory lives beside the backend app / at a configurable path.
    env = os.environ.get("OV_MODELS_DIR")
    if env:
        return env
    # Default: <repo>/backend/ai/segmentation/models
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


# Registered models. Add new entries here as trained checkpoints become
# available. A model is considered "available" only if its checkpoint file
# exists on disk — nothing is fabricated.
REGISTERED_MODELS: dict[str, RegisteredModel] = {
    "bone_1": RegisteredModel(
        id="bone_1",
        name="Bone Segmentation",
        version="1.0",
        task="binary_segmentation",
        labels=("background", "bone"),
        framework="MONAI/PyTorch",
        target_spacing=(1.0, 1.0, 1.0),
        checkpoint_filename="bone_1.pt",
        architecture="unet3d",
    ),
}


def list_models() -> list[dict]:
    """Return metadata for all registered models, including availability."""
    out = []
    mdir = _models_dir()
    for mid, m in REGISTERED_MODELS.items():
        ckpt_available = False
        ckpt_path = None
        if m.checkpoint_filename:
            ckpt_path = os.path.join(mdir, m.checkpoint_filename)
            ckpt_available = os.path.isfile(ckpt_path)
        out.append(
            {
                "id": mid,
                "name": m.name,
                "version": m.version,
                "task": m.task,
                "labels": list(m.labels),
                "framework": m.framework,
                "target_spacing": list(m.target_spacing) if m.target_spacing else None,
                "checkpoint_path": ckpt_path,
                "checkpoint_available": ckpt_available,
            }
        )
    return out


def get_model(model_id: str) -> RegisteredModel:
    m = REGISTERED_MODELS.get(model_id)
    if m is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(f"Unknown segmentation model '{model_id}'.", code="model_not_found")
    return m


def checkpoint_for(model_id: str) -> str | None:
    m = get_model(model_id)
    if not m.checkpoint_filename:
        return None
    path = os.path.join(_models_dir(), m.checkpoint_filename)
    if not os.path.isfile(path):
        return None
    return path


def models_dir() -> str:
    return _models_dir()
