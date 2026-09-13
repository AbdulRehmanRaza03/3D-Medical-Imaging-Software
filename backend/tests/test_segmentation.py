"""Tests for the Phase 3 AI segmentation infrastructure (pure-Python parts)."""
from __future__ import annotations

import numpy as np
import pytest

from ai.segmentation import postprocessing, preprocessing, registry
from ai.segmentation.metrics import dice_coefficient, iou, precision, recall
from ai.segmentation.service import compute_label_stats


def test_registry_has_bone_model():
    models = registry.list_models()
    ids = [m["id"] for m in models]
    assert "bone_1" in ids
    bone = models[ids.index("bone_1")]
    assert bone["labels"] == ["background", "bone"]
    assert bone["framework"] == "MONAI/PyTorch"


def test_registry_checkpoint_not_available_without_weights():
    # No checkpoint file exists by default, so checkpoint_for returns None.
    assert registry.checkpoint_for("bone_1") is None


def test_registry_unknown_model_raises():
    with pytest.raises(Exception):
        registry.get_model("does_not_exist")


def test_clip_hu_and_normalize():
    vol = np.array([[[-2000.0, 0.0], [1000.0, 4000.0]]], dtype=np.float32)
    clipped = preprocessing.clip_hu(vol, -1024.0, 3071.0)
    assert clipped.min() >= -1024.0
    assert clipped.max() <= 3071.0

    normed = preprocessing.normalize_minmax(clipped)
    assert normed.min() >= -1.0
    assert normed.max() <= 1.0


def test_postprocess_threshold_binary():
    probs = np.zeros((2, 4, 4, 4), dtype=np.float32)
    probs[1, 1:3, 1:3, 1:3] = 0.9
    probs[0] = 1.0 - probs[1]
    mask = postprocessing.postprocess(probs, (1.0, 1.0, 1.0), postprocessing.PostProcessingConfig(
        remove_small_components=False,
        keep_largest_connected_component=False,
    ))
    assert mask.shape == (4, 4, 4)
    assert mask.sum() == 2 * 2 * 2  # 2x2x2 foreground


def test_postprocess_keep_largest_component():
    mask = np.zeros((10, 10, 10), dtype=np.uint8)
    mask[1:4, 1:4, 1:4] = 1  # large
    mask[8, 8, 8] = 1  # single isolated voxel

    from ai.segmentation.config import PostProcessingConfig
    cfg = PostProcessingConfig(keep_largest_connected_component=True)
    # Reuse a helper path via postprocess using a probability map is awkward here;
    # test keep_largest_component directly.
    out = postprocessing.keep_largest_component(mask)
    assert out.sum() == 27  # only the 3x3x3 block remains


def test_keep_largest_component_drops_small():
    mask = np.zeros((8, 8, 8), dtype=np.uint8)
    mask[1:5, 1:5, 1:5] = 1  # 4x4x4 = 64
    mask[7, 7, 7] = 1
    out = postprocessing.keep_largest_component(mask)
    assert out.sum() == 64


def test_metrics():
    pred = np.array([[1, 1, 0], [0, 1, 0]], dtype=bool)
    target = np.array([[1, 1, 0], [0, 0, 0]], dtype=bool)
    # perfect on some, one FP, one FN.
    d = dice_coefficient(pred, target)
    assert 0.0 < d <= 1.0
    assert iou(pred, target) >= 0.0
    assert 0.0 <= precision(pred, target) <= 1.0
    assert 0.0 <= recall(pred, target) <= 1.0


def test_compute_label_stats_physical_volume():
    mask = np.zeros((4, 4, 4), dtype=np.uint8)
    mask[1:3, 1:3, 1:3] = 1  # 2x2x2 = 8 voxels
    spacing = (1.0, 1.0, 2.0)
    stats = compute_label_stats(mask, spacing, label_id=1)
    assert stats["voxel_count"] == 8
    # volume = 8 * (1*1*2) mm3 = 16 mm3 = 0.016 cm3 (rounded to 2 dp = 0.02)
    assert stats["volume_cm3"] == 0.02
    assert stats["bbox_min"] is not None
    assert stats["centroid"] is not None


def test_compute_label_stats_empty():
    mask = np.zeros((4, 4, 4), dtype=np.uint8)
    stats = compute_label_stats(mask, (1.0, 1.0, 1.0), label_id=1)
    assert stats["voxel_count"] == 0
    assert stats["volume_cm3"] == 0.0
    assert stats["bbox_min"] is None
