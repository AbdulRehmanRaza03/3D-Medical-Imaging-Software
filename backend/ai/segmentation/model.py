"""Segmentation model architectures (MONAI / PyTorch).

The default is a 3D U-Net. Model loading uses MONAI's ``UNet`` for consistency
and to allow easy swapping (SegResNet, UNETR, Swin UNETR) later.

All torch/MONAI imports are *lazy* (inside functions) so the application and
its tests run even without the ML runtime installed.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _pytorch_available() -> bool:
    """Return True only if torch can actually be imported and a tensor created."""
    try:
        import torch  # noqa: F401

        torch.zeros(1)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("PyTorch unavailable: %s", exc)
        return False


def build_unet3d(
    in_channels: int = 1,
    out_channels: int = 2,
    channels: tuple[int, ...] = (16, 32, 64, 128, 256),
    strides: tuple[int, ...] = (2, 2, 2, 2),
):
    """Build a MONAI 3D U-Net for segmentation.

    ``out_channels`` = number of segmentation classes (2 for binary bone).
    """
    from monai.networks.nets import UNet

    return UNet(
        spatial_dims=3,
        in_channels=in_channels,
        out_channels=out_channels,
        channels=channels,
        strides=strides,
        num_res_units=2,
        norm="instance",
    )


def build_model_for(model_id: str, out_channels: int = 2):
    """Instantiate the model architecture for a registered model ID."""
    from ai.segmentation.registry import get_model

    m = get_model(model_id)
    if m.architecture in ("unet3d", "unet"):
        return build_unet3d(in_channels=1, out_channels=out_channels)
    raise ValueError(f"Unsupported architecture: {m.architecture}")
