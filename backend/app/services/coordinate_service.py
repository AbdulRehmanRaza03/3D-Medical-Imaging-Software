"""Coordinate system: voxel ↔ image ↔ physical (world) conversions.

This module is the single source of truth for how volumetric indices map to
physical patient/world coordinates. Getting this wrong would corrupt MPR views
and measurements.

Conventions
-----------
* The stored volume array is indexed ``data[z, y, x]`` (depth, height, width),
  i.e. axis 0 = slice/axial axis, axis 1 = row axis, axis 2 = column axis.
* ``dimensions = (width, height, depth)`` in voxel-count order (x, y, z).
* ``spacing = (sx, sy, sz)`` are the physical sizes of one voxel along each axis
  (x = column, y = row, z = slice), in mm.
* ``origin`` is the physical coordinate of the centre of the first voxel
  ``(0, 0, 0)`` in index space, in mm.
* ``direction`` is a 3x3 row-major direction-cosine matrix. Row ``i`` is the
  unit vector (in patient LPS) of the positive voxel axis ``i``, where
  ``i = 0 → column/x``, ``i = 1 → row/y``, ``i = 2 → slice/z``.

Physical coordinate of a voxel index ``(ix, iy, iz)``:

    world = origin + direction @ (index * spacing)

and the inverse maps a world point to a (possibly fractional) voxel index.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CoordinateSystem:
    """Encapsulates the affine mapping between voxel and physical space."""

    spacing: tuple[float, float, float]
    origin: tuple[float, float, float]
    direction: tuple[float, ...]  # 9-element row-major

    @property
    def _matrix(self) -> np.ndarray:
        return np.array(self.direction, dtype=float).reshape(3, 3)

    @property
    def _spacing_diag(self) -> np.ndarray:
        return np.diag(np.array(self.spacing, dtype=float))

    @property
    def affine(self) -> np.ndarray:
        """4x4 affine matrix mapping voxel (ix,iy,iz) -> world (x,y,z)."""
        m = self._matrix @ self._spacing_diag
        o = np.array(self.origin, dtype=float)
        aff = np.eye(4, dtype=float)
        aff[:3, :3] = m
        aff[:3, 3] = o
        return aff

    def voxel_to_world(self, index: tuple[float, float, float]) -> tuple[float, float, float]:
        """Map a (possibly fractional) voxel index to physical mm."""
        v = np.array(index, dtype=float)
        w = self._matrix @ (self._spacing_diag @ v) + np.array(self.origin, dtype=float)
        return (float(w[0]), float(w[1]), float(w[2]))

    def world_to_voxel(self, world: tuple[float, float, float]) -> tuple[float, float, float]:
        """Map a physical mm coordinate to a (possibly fractional) voxel index.

        Returns fractional indices; callers clamp/round as needed.
        """
        w = np.array(world, dtype=float)
        inv = np.linalg.inv(self._matrix @ self._spacing_diag)
        v = inv @ (w - np.array(self.origin, dtype=float))
        return (float(v[2]), float(v[1]), float(v[0]))  # → (z, y, x)


def build_coordinate_system(
    spacing: tuple[float, float, float],
    origin: tuple[float, float, float],
    direction: tuple[float, ...],
) -> CoordinateSystem:
    """Build a validated coordinate system."""
    if len(spacing) != 3:
        raise ValueError("spacing must have 3 components")
    if len(origin) != 3:
        raise ValueError("origin must have 3 components")
    if len(direction) != 9:
        raise ValueError("direction must have 9 components")

    # Guard against degenerate (invertible) direction matrix.
    m = np.array(direction, dtype=float).reshape(3, 3)
    if abs(np.linalg.det(m)) < 1e-9:
        raise ValueError("direction matrix is singular")

    return CoordinateSystem(spacing=tuple(float(s) for s in spacing),
                            origin=tuple(float(o) for o in origin),
                            direction=tuple(float(d) for d in direction))
