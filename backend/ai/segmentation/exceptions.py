"""Segmentation exceptions with user-facing messages."""
from __future__ import annotations

from app.core.exceptions import OrthoVisionError


class SegRuntimeUnavailableError(OrthoVisionError):
    """PyTorch / MONAI runtime is not importable (e.g. missing MSVC runtime)."""

    status_code = 422
    code = "seg_runtime_unavailable"

    def __init__(self):
        super().__init__(
            "AI segmentation runtime (PyTorch/MONAI) is not available. "
            "Install the Microsoft Visual C++ Redistributable "
            "(https://aka.ms/vs/17/release/vc_redist.x64.exe) and restart.",
            code=self.code,
        )


class ModelCheckpointMissingError(OrthoVisionError):
    """No trained model checkpoint is configured for the requested model."""

    status_code = 422
    code = "model_checkpoint_missing"

    def __init__(self, model_id: str):
        super().__init__(
            f"Segmentation could not be completed because the model checkpoint "
            f"for '{model_id}' is not configured. Place the checkpoint weights "
            f"under the configured models directory.",
            code=self.code,
        )


class SegmentationError(OrthoVisionError):
    """Generic segmentation failure with a useful message."""

    status_code = 422
    code = "segmentation_failed"
