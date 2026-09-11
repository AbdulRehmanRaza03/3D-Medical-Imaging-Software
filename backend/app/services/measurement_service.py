"""Measurements on reconstructed meshes using physical world coordinates.

Distances/angles are computed from the actual vertex coordinates (mm), never
from screen pixels, so they reflect true anatomical dimensions.
"""
from __future__ import annotations

import numpy as np

from app.core.exceptions import ValidationError


def distance_mm(p0: list[float], p1: list[float]) -> float:
    """Euclidean distance between two 3D points (mm)."""
    a = np.array(p0, dtype=float)
    b = np.array(p1, dtype=float)
    return float(np.linalg.norm(b - a))


def angle_deg(p0: list[float], p1: list[float], p2: list[float]) -> float:
    """Angle at vertex ``p1`` formed by (p0, p1, p2), in degrees."""
    a = np.array(p0, dtype=float)
    b = np.array(p1, dtype=float)
    c = np.array(p2, dtype=float)
    v0 = a - b
    v1 = c - b
    n0 = np.linalg.norm(v0)
    n1 = np.linalg.norm(v1)
    if n0 == 0 or n1 == 0:
        raise ValidationError("Angle points must be distinct.", code="invalid_angle")
    cos_theta = np.clip(np.dot(v0, v1) / (n0 * n1), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_theta)))
