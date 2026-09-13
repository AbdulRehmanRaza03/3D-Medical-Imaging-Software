"""Segmentation post-processing: mask cleanup, component filtering, labels."""
from __future__ import annotations

import numpy as np
from scipy import ndimage

from ai.segmentation.config import PostProcessingConfig


def argmax_to_mask(probs: np.ndarray) -> np.ndarray:
    """Convert a (C, D, H, W) probability map to an integer label map."""
    return np.argmax(probs, axis=0).astype(np.uint8)


def threshold_binary(probs: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """For a single-class score map, threshold to a binary mask."""
    if probs.ndim == 4:
        score = probs[1]  # channel 1 = foreground
    else:
        score = probs
    return (score > threshold).astype(np.uint8)


def remove_small_components(mask: np.ndarray, min_voxels: int) -> np.ndarray:
    """Remove connected components smaller than ``min_voxels``."""
    labeled, num = ndimage.label(mask)
    if num <= 1:
        return mask
    sizes = ndimage.sum(mask, labeled, range(1, num + 1))
    keep = np.zeros(num + 1, dtype=bool)
    keep[0] = False
    for i in range(1, num + 1):
        if sizes[i - 1] >= min_voxels:
            keep[i] = True
    return keep[labeled].astype(np.uint8, copy=False)


def keep_largest_component(mask: np.ndarray) -> np.ndarray:
    """Keep only the largest connected component."""
    labeled, num = ndimage.label(mask)
    if num == 0:
        return mask
    sizes = ndimage.sum(mask, labeled, range(1, num + 1))
    largest = int(np.argmax(sizes)) + 1
    return (labeled == largest).astype(np.uint8)


def fill_holes(mask: np.ndarray) -> np.ndarray:
    """Fill enclosed holes in the binary mask."""
    return ndimage.binary_fill_holes(mask).astype(np.uint8)


def postprocess(
    probs: np.ndarray,
    spacing: tuple[float, float, float],
    config: PostProcessingConfig | None = None,
) -> np.ndarray:
    """Convert probabilities to a cleaned binary mask.

    ``spacing`` is used to convert a physical volume threshold into a voxel
    count threshold for small-component removal.
    """
    config = config or PostProcessingConfig()

    mask = threshold_binary(probs)
    mask = mask.astype(np.uint8)

    if config.remove_small_components or config.keep_largest_connected_component:
        voxel_volume_mm3 = spacing[0] * spacing[1] * spacing[2]
        min_voxels = max(1, int(config.min_component_volume_mm3 / voxel_volume_mm3))
        if config.keep_largest_connected_component:
            mask = keep_largest_component(mask)
        else:
            mask = remove_small_components(mask, min_voxels)

    if config.fill_holes:
        mask = fill_holes(mask)

    return mask
