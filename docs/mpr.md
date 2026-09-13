# Multiplanar Reconstruction (MPR)

MPR lets a single 3D CT volume be examined along three orthogonal anatomical
planes without creating any duplicate data.

## Volume representation

Phase 1 stores the CT volume as a NumPy array with shape
`(depth, height, width)` (i.e. indexed `data[z, y, x]`), plus:

- `spacing = (sx, sy, sz)` — physical size of one voxel per axis (mm)
- `origin` — physical coordinate of the first voxel `(0,0,0)`
- `direction` — 3×3 row-major direction-cosine matrix
- `dimensions = (width, height, depth)`

## Plane extraction

Each plane is a slice along one volume axis:

| Plane    | Constant axis | Extraction          | Resulting shape (rows, cols) |
| -------- | ------------- | ------------------- | ---------------------------- |
| Axial    | z (depth)     | `data[z, :, :]`     | (y, x)                       |
| Coronal  | y (height)    | `data[:, y, :]`     | (z, x)                       |
| Sagittal | x (width)     | `data[:, :, x]`     | (z, y)                       |

The slice count per plane equals the size of the axis being sliced:

- Axial: `depth` slices (one per z)
- Coronal: `height` slices (one per y)
- Sagittal: `width` slices (one per x)

This is implemented in `backend/app/services/mpr_service.py`
(`extract_plane` and `plane_metadata`).

## Physical dimensions

The physical size of each plane is computed from the voxel spacing. For a
non-isotropic volume with `spacing = (0.7, 0.7, 2.0)`:

- Axial image: `width * 0.7 × height * 0.7` mm
- Coronal image: `width * 0.7 × depth * 2.0` mm (tall because z is thick)
- Sagittal image: `height * 0.7 × depth * 2.0` mm

This respects anisotropic voxel spacing so views are never distorted.

## API

- `GET /api/v1/studies/{id}/volume` — volume metadata (shape/spacing/origin/direction)
- `GET /api/v1/studies/{id}/mpr/{axial|coronal|sagittal}?index=&width=&level=` —
  windowed PNG slice
- `GET /api/v1/studies/{id}/coordinates?x=&y=&z=` — world → voxel + HU
- `GET /api/v1/studies/{id}/voxel?x=&y=&z=` — voxel → world + HU
