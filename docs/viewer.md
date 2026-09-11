# Viewer

The Medical Viewer combines a 2D axial slice viewer and a 3D model viewer in a
single workspace.

## 2D slice viewer

- Renders windowed slices to a `<canvas>` (not hundreds of DOM nodes), keeping
  the interface responsive.
- Slice navigation: slider, mouse-wheel scroll (Ctrl/⌘+wheel = zoom).
- Zoom and pan with drag.
- Window/level adjustment with presets (Bone, Soft tissue, Lung) and custom
  sliders.
- Displays `Slice X / Total`.

Slices are served by the backend as windowed 8-bit PNG (base64) with the
current window/level applied server-side.

## 3D viewer

Built with React Three Fiber + Drei:

- Orbit rotation, zoom, pan.
- Reset camera.
- Wireframe toggle, grid toggle, axes (gizmo) toggle.
- Medical-styled dark background and lighting.
- The model is loaded from a binary GLB endpoint (`/models/{id}/mesh`).

## Measurements

- **Distance** — two points → Euclidean distance in mm.
- **Angle** — three points → angle in degrees.

Points are picked in the 3D scene and measured in **physical world coordinates**
(never screen pixels). The measurement is submitted to the backend for
calculation and persistence.

## Model information

Displays real study/model metadata, e.g.:

```
Modality: CT
Slices: 164
Dimensions: 512 × 512
Voxel spacing: 0.68 × 0.68 × 1.0 mm
Reconstruction: Marching Cubes
Threshold: 300 HU
Vertices: 124,520
Triangles: 249,018
Physical size: 348 × 348 × 164 mm
```
