"""Segmentation pipeline orchestration.

Wires preprocessing → inference → post-processing → mask persistence →
physical metrics. This is the single entry point used by the job service.
"""
from __future__ import annotations

import json
import logging
import time

import numpy as np

from ai.segmentation import (
    inference,
    postprocessing,
    preprocessing,
    registry,
)
from ai.segmentation.config import (
    InferenceConfig,
    PostProcessingConfig,
    PreprocessingConfig,
)
from ai.segmentation.exceptions import (
    ModelCheckpointMissingError,
    SegRuntimeUnavailableError,
    SegmentationError,
)

logger = logging.getLogger(__name__)

STAGE_MESSAGES = [
    "Preparing volume…",
    "Preprocessing…",
    "Running AI model…",
    "Generating segmentation…",
    "Completed",
]


def compute_label_stats(
    mask: np.ndarray,
    spacing: tuple[float, float, float],
    label_id: int = 1,
) -> dict:
    """Compute voxel count, physical volume, bbox, and centroid for a label."""
    binary = (mask == label_id)
    voxel_count = int(binary.sum())
    voxel_vol_mm3 = spacing[0] * spacing[1] * spacing[2]
    volume_cm3 = voxel_count * voxel_vol_mm3 / 1000.0

    bbox_min = bbox_max = centroid = None
    if voxel_count > 0:
        zs, ys, xs = np.nonzero(binary)
        bbox_min = [
            float(xs.min()) * spacing[0],
            float(ys.min()) * spacing[1],
            float(zs.min()) * spacing[2],
        ]
        bbox_max = [
            float(xs.max()) * spacing[0],
            float(ys.max()) * spacing[1],
            float(zs.max()) * spacing[2],
        ]
        centroid = [
            float(xs.mean()) * spacing[0],
            float(ys.mean()) * spacing[1],
            float(zs.mean()) * spacing[2],
        ]

    return {
        "id": label_id,
        "voxel_count": voxel_count,
        "volume_cm3": round(volume_cm3, 2),
        "bbox_min": bbox_min,
        "bbox_max": bbox_max,
        "centroid": centroid,
    }


def run_segmentation(
    *,
    model_id: str,
    volume: np.ndarray,  # (D, H, W) float32 HU
    spacing: tuple[float, float, float],
    preprocess_cfg: PreprocessingConfig | None = None,
    inference_cfg: InferenceConfig | None = None,
    postprocess_cfg: PostProcessingConfig | None = None,
    progress_cb=None,
) -> dict:
    """Run the full AI segmentation pipeline on a CT volume.

    Returns a dict with ``mask`` (np.uint8), ``labels`` (list of label stats),
    ``device``, and ``duration_sec``.

    Raises ``SegRuntimeUnavailableError`` if torch/MONAI can't import, and
    ``ModelCheckpointMissingError`` if no checkpoint is configured.
    """
    checkpoint = registry.checkpoint_for(model_id)
    if checkpoint is None:
        raise ModelCheckpointMissingError(model_id)

    if not inference.torch_available():
        raise SegRuntimeUnavailableError()

    start = time.monotonic()

    def _stage(i: int):
        if progress_cb:
            progress_cb(i / len(STAGE_MESSAGES), STAGE_MESSAGES[i])

    _stage(0)  # Preparing volume
    if volume.ndim != 3:
        raise SegmentationError("Volume must be 3D for segmentation.", code="bad_volume")

    _stage(1)  # Preprocessing
    input_tensor = preprocessing.preprocess(volume, preprocess_cfg)

    # Build and load model.
    import torch  # noqa: F401  (guaranteed available after torch_available check)

    from ai.segmentation.model import build_model_for

    device = inference.resolve_device(inference_cfg.device if inference_cfg else "auto")
    model = build_model_for(model_id, out_channels=2)
    model = inference.load_checkpoint(model, checkpoint, device)
    model.eval()

    _stage(2)  # Running model
    # Preprocess returns shape (1,1,D',H',W') where D' may be padded.
    orig_shape = volume.shape
    probs = inference.run_inference(model, input_tensor, inference_cfg)

    # Undo any padding applied during preprocessing to realign with source.
    probs = probs[:, :, : orig_shape[0], : orig_shape[1], : orig_shape[2]]

    _stage(3)  # Generating segmentation
    mask = postprocessing.postprocess(probs, spacing, postprocess_cfg)

    # Compute per-label stats.
    labels = [compute_label_stats(mask, spacing, label_id=1)]

    duration = time.monotonic() - start

    _stage(4)  # Completed
    if progress_cb:
        progress_cb(1.0, "Completed")

    return {
        "mask": mask,
        "labels": labels,
        "device": str(device),
        "duration_sec": round(duration, 2),
    }
