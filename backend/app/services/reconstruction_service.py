"""3D reconstruction: thresholding, binary mask, Marching Cubes, mesh cleanup.

The pipeline is:
  CT volume (HU) -> threshold -> binary mask -> (optional) morphological
  cleanup -> Marching Cubes -> vertices/faces -> mesh cleanup -> mesh.

Critical detail: Marching Cubes operates on a *regular grid index-space*; the
resulting vertex coordinates must be multiplied by the physical voxel spacing so
the mesh represents real anatomy rather than a spacerially-distorted model.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage
from skimage import measure

from app.core.exceptions import ProcessingError
from app.services.volume_service import Volume

# Air is typically <= -900 HU and water ~0 HU; bone is ~> 300 HU. A default of
# 300 HU isolates dense cortical/trabecular bone while ignoring soft tissue.
DEFAULT_BONE_THRESHOLD_HU = 300.0


@dataclass
class MeshData:
    """A reconstructed anatomical surface mesh in physical (mm) coordinates."""

    vertices: np.ndarray  # (N, 3) float32, physical mm
    faces: np.ndarray  # (M, 3) int64
    bbox_min: tuple[float, float, float]
    bbox_max: tuple[float, float, float]
    physical_size: tuple[float, float, float]
    threshold_hu: float


def threshold_mask(volume: Volume, threshold_hu: float) -> np.ndarray:
    """Create a binary mask of voxels >= ``threshold_hu`` (HU)."""
    return volume.data >= threshold_hu


def clean_mask(mask: np.ndarray, remove_small: bool, min_fraction: float) -> np.ndarray:
    """Optional lightweight morphological cleanup.

    Only removes tiny disconnected components when requested; this is safe with
    respect to anatomy because whole disconnected speckle is removed, not the
    surface itself.
    """
    if not remove_small:
        return mask

    labeled, num_features = ndimage.label(mask)
    if num_features == 0:
        return mask

    if num_features == 1:
        return mask

    sizes = ndimage.sum(mask, labeled, range(1, num_features + 1))
    total = mask.size
    keep = np.zeros(num_features + 1, dtype=bool)
    keep[0] = False  # background
    for i in range(1, num_features + 1):
        if sizes[i - 1] / total >= min_fraction:
            keep[i] = True

    return keep[labeled].astype(np.uint8, copy=False)


def marching_cubes_mesh(mask: np.ndarray, spacing: tuple[float, float, float]) -> tuple[np.ndarray, np.ndarray]:
    """Run Marching Cubes and scale vertices to physical spacing.

    ``skimage.measure.marching_cubes`` operates in voxel index space. To produce
    a physically accurate model we multiply vertex coordinates by the
    (sx, sy, sz) voxel spacing. This is *essential* for anisotropic CT volumes
    (where slice thickness >> pixel spacing); skipping it produces a model that
    is dramatically squashed or stretched relative to real anatomy.
    """
    if not mask.any():
        raise ProcessingError("Threshold produced an empty mask; no voxels matched.")

    # Pad by one voxel to avoid surface truncation at volume boundary.
    padded = np.pad(mask, 1, mode="constant", constant_values=False)

    verts, faces, _normals, _values = measure.marching_cubes(
        padded, level=0.5, step_size=1
    )

    # Undo padding offset, then convert index -> physical space.
    verts = verts - 1.0
    verts = verts.astype(np.float32)
    verts[:, 0] *= spacing[0]
    verts[:, 1] *= spacing[1]
    verts[:, 2] *= spacing[2]

    return verts, faces.astype(np.int64)


def clean_mesh(
    verts: np.ndarray,
    faces: np.ndarray,
    smoothing_iterations: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Lightweight mesh cleanup: remove degenerate faces and unused vertices.

    Optionally applies a small number of Laplacian smoothing iterations. This is
    intentionally conservative — aggressive smoothing destroys anatomical detail.
    """
    # Remove degenerate faces (two or more identical vertex indices).
    keep = np.ones(len(faces), dtype=bool)
    a, b, c = faces[:, 0], faces[:, 1], faces[:, 2]
    degenerate = (a == b) | (b == c) | (a == c)
    keep[degenerate] = False
    faces = faces[keep]

    if faces.size == 0:
        raise ProcessingError("Mesh contains no valid faces after cleanup.")

    # Drop unused vertices and remap indices.
    used = np.unique(faces)
    if used.size < verts.shape[0]:
        remap = np.full(verts.shape[0], -1, dtype=np.int64)
        remap[used] = np.arange(used.size, dtype=np.int64)
        faces = remap[faces]
        verts = verts[used]

    if smoothing_iterations and smoothing_iterations > 0:
        for _ in range(int(smoothing_iterations)):
            verts = _laplacian_smooth(verts, faces)

    return verts, faces


def _laplacian_smooth(verts: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """One pass of uniform Laplacian smoothing (uniform weights)."""
    new_verts = verts.copy()
    counts = np.zeros(len(verts), dtype=np.float32)
    # Accumulate neighbor positions via triangle edges.
    for a, b in faces:
        new_verts[a] += verts[b]
        new_verts[b] += verts[a]
        counts[a] += 1
        counts[b] += 1
    valid = counts > 0
    new_verts[valid] = verts[valid] + (new_verts[valid] / counts[valid, None] - verts[valid]) * 0.5
    return new_verts


def bbox_and_size(verts: np.ndarray) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    """Compute bounding box and physical size from vertices."""
    if verts.shape[0] == 0:
        raise ProcessingError("Mesh has no vertices.")
    bmin = verts.min(axis=0)
    bmax = verts.max(axis=0)
    bbox_min = tuple(float(v) for v in bmin)
    bbox_max = tuple(float(v) for v in bmax)
    size = tuple(float(v) for v in (bmax - bmin))
    return bbox_min, bbox_max, size


def reconstruct_bone(
    volume: Volume,
    threshold_hu: float = DEFAULT_BONE_THRESHOLD_HU,
    remove_small_components: bool = True,
    min_component_fraction: float = 0.001,
    smoothing_iterations: int = 0,
) -> MeshData:
    """Run the full bone reconstruction pipeline on a CT volume."""
    mask = threshold_mask(volume, threshold_hu)
    mask = clean_mask(mask, remove_small_components, min_component_fraction)
    verts, faces = marching_cubes_mesh(mask, volume.spacing)
    verts, faces = clean_mesh(verts, faces, smoothing_iterations)
    bbox_min, bbox_max, size = bbox_and_size(verts)
    return MeshData(
        vertices=verts,
        faces=faces,
        bbox_min=bbox_min,
        bbox_max=bbox_max,
        physical_size=size,
        threshold_hu=threshold_hu,
    )
