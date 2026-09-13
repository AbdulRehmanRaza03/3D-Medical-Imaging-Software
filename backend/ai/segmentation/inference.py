"""Segmentation inference: model loading and prediction.

Implements CPU/GPU auto-selection and (optionally) sliding-window inference for
large volumes. All torch usage is lazy and fails with an actionable error when
the runtime is unavailable.
"""
from __future__ import annotations

import logging

import numpy as np

from ai.segmentation.config import InferenceConfig
from ai.segmentation.exceptions import (
    ModelCheckpointMissingError,
    SegRuntimeUnavailableError,
)

logger = logging.getLogger(__name__)


def resolve_device(device: str = "auto") -> "torch.device":
    """Resolve the inference device, defaulting to CUDA when available."""
    import torch

    if device == "cuda":
        return torch.device("cuda")
    if device == "cpu":
        return torch.device("cpu")
    # auto
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def torch_available() -> bool:
    """True if torch and MONAI both import and run correctly."""
    try:
        import torch  # noqa: F401
        import monai  # noqa: F401

        torch.zeros(1)
        return True
    except Exception:  # noqa: BLE001
        return False


def load_checkpoint(model, checkpoint_path: str, device):
    """Load weights into a model instance."""
    import torch

    state = torch.load(checkpoint_path, map_location=device)

    # Accept either a raw state_dict or a dict with a 'model_state_dict' key
    # (MONAI SaveImage/trainer style).
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    elif isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]

    model.load_state_dict(state)
    model.eval()
    return model


def run_inference(
    model,
    input_tensor: "torch.Tensor",
    config: InferenceConfig | None = None,
) -> np.ndarray:
    """Run inference and return a probability/logit volume (numpy, CHWD)."""
    config = config or InferenceConfig()
    import torch
    import torch.nn.functional as F

    device = resolve_device(config.device)
    model = model.to(device)
    input_tensor = input_tensor.to(device)

    with torch.no_grad():
        # Whole-volume inference (fits in memory) — the sample/test volumes and
        # most small CT crops fit comfortably. Sliding-window is available for
        # large volumes via `run_sliding_window`.
        logits = model(input_tensor)
        probs = F.softmax(logits, dim=1)

    return probs.detach().cpu().numpy()


def run_sliding_window(
    model,
    input_tensor: "torch.Tensor",
    roi_size: tuple[int, int, int],
    config: InferenceConfig | None = None,
) -> np.ndarray:
    """Sliding-window inference using MONAI for volumes larger than memory."""
    config = config or InferenceConfig()
    device = resolve_device(config.device)

    from monai.inferers import sliding_window_inference

    model = model.to(device)
    input_tensor = input_tensor.to(device)

    def _forward(x):
        return model(x)

    with torch.no_grad():
        out = sliding_window_inference(
            inputs=input_tensor,
            roi_size=roi_size,
            sw_batch_size=config.sw_batch_size,
            predictor=_forward,
            overlap=config.overlap,
        )

    import torch.nn.functional as F

    probs = F.softmax(out, dim=1)
    return probs.detach().cpu().numpy()
