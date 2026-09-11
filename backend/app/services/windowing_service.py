"""CT windowing/leveling utilities for 2D slice display."""
from __future__ import annotations

import numpy as np

# Conservative presets. These are common starting points but are NOT universal
# truth for every scanner — they give a sensible default display window.
WINDOW_PRESETS: dict[str, tuple[float, float]] = {
    "bone": (1800.0, 400.0),        # (width, level)
    "soft_tissue": (400.0, 40.0),
    "lung": (1500.0, -600.0),
    "brain": (80.0, 40.0),
}


def apply_window(hu: np.ndarray, width: float, level: float) -> np.ndarray:
    """Map HU values into an 8-bit display range using window width/level.

    Returns a uint8 array suitable for direct rendering to a canvas.
    """
    if width <= 0:
        width = 1.0
    lower = level - width / 2.0
    upper = level + width / 2.0

    img = hu.astype(np.float32)
    # Linear map [lower, upper] -> [0, 255].
    scaled = (img - lower) * (255.0 / width)
    scaled = np.clip(scaled, 0.0, 255.0)
    return scaled.astype(np.uint8)


def default_window(series_hu_min: float, series_hu_max: float) -> tuple[float, float]:
    """Choose a default window if none is present in the DICOM metadata."""
    # Heuristic: if the range is narrow use a general soft-tissue-ish window.
    rng = series_hu_max - series_hu_min
    if rng <= 300:
        return WINDOW_PRESETS["brain"]
    return WINDOW_PRESETS["soft_tissue"]
