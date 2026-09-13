"""Medical-image preprocessing for segmentation inference.

Transforms the canonical CT volume (Hounsfield Units) into a normalized float
tensor suitable for the model, without modifying the original volume. The
original CT array is never mutated.
"""
from __future__ import annotations

import numpy as np

from ai.segmentation.config import PreprocessingConfig
from ai.segmentation.exceptions import SegmentationError


def clip_hu(volume: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Clip Hounsfield units to a valid/intended range (copy)."""
    return np.clip(volume.astype(np.float32), lo, hi)


def normalize_minmax(volume: np.ndarray, lo: float = -1.0, hi: float = 1.0) -> np.ndarray:
    """Normalize a clipped volume into [lo, hi] using the clip bounds.

    Uses fixed bounds of [-1024, 3071] (the canonical CT window) so inference is
    intensity-consistent regardless of the dataset's actual min/max.
    """
    span = 3071.0 - (-1024.0)
    return (volume - (-1024.0)) / span * (hi - lo) + lo


def to_channel_tensor(arr: np.ndarray) -> "torch.Tensor":
    """Convert a (D,H,W) float32 array to a (1,1,D,H,W) tensor (NCHWD)."""
    import torch

    t = torch.from_numpy(np.ascontiguousarray(arr))
    return t.unsqueeze(0).unsqueeze(0)


def preprocess(
    volume: np.ndarray,  # (D, H, W) float32 HU
    config: PreprocessingConfig | None = None,
) -> "torch.Tensor":
    """Preprocess a CT volume into a normalized model input tensor.

    Returns a (1, 1, D, H, W) tensor. The input ``volume`` is never modified.
    """
    config = config or PreprocessingConfig()

    if volume.ndim != 3:
        raise SegmentationError(
            f"Expected a 3D volume, got {volume.ndim}D.", code="bad_volume"
        )

    if not _numpy_ok():
        raise SegmentationError("NumPy is required for preprocessing.", code="runtime")

    arr = clip_hu(volume, config.clip_hu_min, config.clip_hu_max)

    if config.normalize:
        arr = normalize_minmax(arr, config.normalize_min, config.normalize_max)

    tensor = to_channel_tensor(arr)

    if config.pad_to_divisible and config.pad_to_divisible > 1:
        p = config.pad_to_divisible
        tensor = _pad_to_divisible(tensor, p)

    return tensor


def _numpy_ok() -> bool:
    return True


def _pad_to_divisible(tensor: "torch.Tensor", divisor: int) -> "torch.Tensor":
    import torch.nn.functional as F

    d, h, w = tensor.shape[-3:]
    pd = (divisor - d % divisor) % divisor
    ph = (divisor - h % divisor) % divisor
    pw = (divisor - w % divisor) % divisor
    if pd == 0 and ph == 0 and pw == 0:
        return tensor
    # Pad (W, H, D) order for F.pad on last three dims.
    return F.pad(tensor, (0, pw, 0, ph, 0, pd))
