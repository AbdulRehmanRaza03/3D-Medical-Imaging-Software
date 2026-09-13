# Coordinate System

OrthoVision AI uses an explicit, tested mapping between **voxel indices** and
**physical (world) coordinates**. Getting this wrong would corrupt MPR views
and measurements, so it is centralized in one module and covered by tests.

## Axes

The volume array is indexed `data[z, y, x]`:

| Index | Axis | Meaning                    | Physical spacing |
| ----- | ---- | -------------------------- | ---------------- |
| `x`   | 0    | column (left–right)        | `sx`             |
| `y`   | 1    | row (anterior–posterior)   | `sy`             |
| `z`   | 2    | slice (superior–inferior)  | `sz`             |

## Mapping

The physical coordinate of a voxel `(ix, iy, iz)` is:

```
world = origin + direction @ (index · spacing)
```

where `direction` is the 3×3 row-major direction-cosine matrix (row `i` is the
unit vector of the positive voxel axis `i` in patient LPS coordinates).

The inverse maps a world point back to a (possibly fractional) voxel index:

```
index = (direction @ diag(spacing))⁻¹ @ (world - origin)
```

## Implementation

`backend/app/services/coordinate_service.py`:

- `CoordinateSystem.voxel_to_world(index) -> (x, y, z)`
- `CoordinateSystem.world_to_voxel(world) -> (z, y, x)`  (note axis order)

The `world_to_voxel` returns `(z, y, x)` to match the volume indexing, while
`voxel_to_world` takes `(x, y, z)` in column/row/slice order. This asymmetry is
deliberate and documented; callers convert explicitly.

## Non-isotropic spacing

With `spacing = (0.7, 0.7, 2.0)`, one voxel step in z is `2.0 mm` while a step
in x/y is `0.7 mm`. The coordinate system and MPR extraction both respect this,
so sagittal/coronal views are vertically stretched to their correct physical
proportions rather than being drawn as if the volume were isotropic.

## Tests

`backend/tests/test_coordinates_mpr.py` verifies:

- voxel → world and world → voxel round-trips
- non-isotropic spacing physical correctness
- rejection of a singular (non-invertible) direction matrix
- per-plane physical dimensions for non-isotropic volumes
