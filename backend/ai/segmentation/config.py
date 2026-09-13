"""Segmentation configuration dataclasses and defaults."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PreprocessingConfig:
    """Configuration for volume preprocessing before inference."""

    target_spacing: tuple[float, float, float] | None = None  # None = keep native
    clip_hu_min: float = -1024.0
    clip_hu_max: float = 3071.0
    normalize: bool = True
    normalize_min: float = -1.0
    normalize_max: float = 1.0
    pad_to_divisible: int = 16  # pad so dims are divisible by this; 0 = disable


@dataclass(frozen=True)
class InferenceConfig:
    """Configuration for model inference."""

    device: str = "auto"  # "auto" | "cpu" | "cuda"
    overlap: float = 0.5  # sliding-window overlap fraction
    sw_batch_size: int = 1  # sliding-window batch size
    roi_size: tuple[int, int, int] | None = None  # window size; None = whole volume


@dataclass(frozen=True)
class PostProcessingConfig:
    """Configuration for segmentation mask post-processing."""

    remove_small_components: bool = True
    min_component_volume_mm3: float = 50.0  # drop components smaller than this
    fill_holes: bool = False
    keep_largest_connected_component: bool = True


@dataclass
class SegmentationLabel:
    """Description of one segmentation label/class."""

    id: int
    name: str
    color: str  # hex for display

    @property
    def display(self) -> str:
        return self.name


# Default label set for binary bone segmentation.
BONE_LABELS: list[SegmentationLabel] = [
    SegmentationLabel(id=0, name="background", color="#000000"),
    SegmentationLabel(id=1, name="bone", color="#38bdf8"),
]
