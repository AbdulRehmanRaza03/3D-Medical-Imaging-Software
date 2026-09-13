"""Segmentation evaluation metrics.

Metrics are computed ONLY against ground-truth annotations (e.g. for research
datasets). They are never used to fabricate accuracy numbers for inference
results without ground truth.
"""
from __future__ import annotations

import numpy as np


def dice_coefficient(pred: np.ndarray, target: np.ndarray, eps: float = 1e-6) -> float:
    """Binary Dice coefficient between two boolean masks."""
    p = pred.astype(bool)
    t = target.astype(bool)
    inter = np.logical_and(p, t).sum()
    return float((2.0 * inter + eps) / (p.sum() + t.sum() + eps))


def iou(pred: np.ndarray, target: np.ndarray, eps: float = 1e-6) -> float:
    """Intersection-over-union (Jaccard) between two boolean masks."""
    p = pred.astype(bool)
    t = target.astype(bool)
    inter = np.logical_and(p, t).sum()
    union = np.logical_or(p, t).sum()
    return float((inter + eps) / (union + eps))


def precision(pred: np.ndarray, target: np.ndarray, eps: float = 1e-6) -> float:
    p = pred.astype(bool)
    t = target.astype(bool)
    tp = np.logical_and(p, t).sum()
    return float((tp + eps) / (p.sum() + eps))


def recall(pred: np.ndarray, target: np.ndarray, eps: float = 1e-6) -> float:
    p = pred.astype(bool)
    t = target.astype(bool)
    tp = np.logical_and(p, t).sum()
    return float((tp + eps) / (t.sum() + eps))
