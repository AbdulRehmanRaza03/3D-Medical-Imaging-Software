# Reconstruction

The 3D reconstruction pipeline converts a CT volume into an anatomical surface
mesh.

## Pipeline

```
CT volume (HU)
  ↓ threshold (e.g. >= 300 HU for bone)
binary mask
  ↓ optional morphological cleanup (remove tiny disconnected components)
  ↓ Marching Cubes (scikit-image)
vertices + faces (index space)
  ↓ scale by voxel spacing
vertices + faces (physical mm)
  ↓ mesh cleanup (remove degenerate faces, drop unused vertices)
final mesh
```

## Thresholding

A voxel belongs to the mask when `HU >= threshold_hu`. The default bone
threshold is **300 HU** (dense cortical/trabecular bone), but this is
configurable — no single threshold is correct for every scanner or anatomy.

## Marching Cubes & spacing (critical)

`skimage.measure.marching_cubes` operates in *voxel index space*. CT volumes are
typically **anisotropic** (in-plane pixel spacing ≪ slice thickness). If the
vertex coordinates were returned without scaling, the resulting model would be
squashed or stretched relative to real anatomy.

Therefore, after marching cubes, vertex coordinates are multiplied by the
`(sx, sy, sz)` voxel spacing to produce a physically accurate model:

```python
verts[:, 0] *= spacing[0]
verts[:, 1] *= spacing[1]
verts[:, 2] *= spacing[2]
```

## Mesh cleanup

- Degenerate faces (repeated vertex indices) are removed.
- Unused vertices are dropped and indices remapped.
- Optional conservative Laplacian smoothing (default off) — aggressive
  smoothing is avoided because it can destroy anatomical detail.
- Bounding box and physical dimensions are computed from the final vertices.

## Output

`MeshData` carries `vertices`, `faces`, `bbox_min`, `bbox_max`,
`physical_size`, and `threshold_hu`.
