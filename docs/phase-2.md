# Phase 2 — Advanced Medical Visualization & MPR

Phase 2 extends the Phase 1 core with a professional **multiplanar
reconstruction (MPR)** workstation and advanced 3D visualization.

## What was added

| Area | Feature |
| ---- | ------- |
| **MPR** | Axial, coronal, and sagittal views extracted from the same CT volume |
| **Synchronization** | Crosshair synchronized across all three 2D planes + 3D reference |
| **Coordinate system** | Explicit voxel ↔ physical (world) coordinate mapping |
| **Window/Level** | Presets (bone/soft-tissue/lung) + mouse-driven interaction |
| **3D** | Opacity control, orthographic/perspective camera, MPR reference planes, clipping |
| **UI/UX** | Full dark medical workstation: left tool rail, 4-panel grid, info bar |

## What is MPR

Multiplanar reconstruction displays the same 3D CT volume along its three
orthogonal axes:

- **Axial** — slice perpendicular to the superior–inferior (z) axis.
- **Coronal** — slice perpendicular to the anterior–posterior (y) axis.
- **Sagittal** — slice perpendicular to the left–right (x) axis.

No new data is created — each plane is simply a re-slice of the existing array
along a different axis. See `mpr.md`.

## Definition of Done (Phase 2)

- [x] Axial / coronal / sagittal views work from the same volume
- [x] Slice navigation (slider + wheel) per plane
- [x] Crosshair synchronization across planes
- [x] Voxel ↔ physical coordinate conversion
- [x] Window/level (presets + manual + mouse interaction)
- [x] Orientation markers per plane
- [x] 3D model opacity
- [x] Orthographic / perspective camera
- [x] MPR reference planes in 3D
- [x] 3D clipping (material clipping planes)
- [x] No regression in Phase 1 (upload, reconstruction, export, measurement)
- [x] Backend + frontend tests pass

## Known limitations

- Clipping planes are exposed via the render material but the UI still exposes
  the full model (no drag-handle plane gizmo in Phase 2).
- Sagittal/coronal orientation labels assume the standard near-axial DICOM
  convention (row→x, col→y); oblique/rotated series may relabel approximated.
- Crosshair updates derive from the three slice indices (voxel cell), not an
  independent interpolated world point; the `coordinates` endpoint is available
  for exact world↔voxel lookup when needed.
