# Viewer Architecture (Phase 2)

The Phase 2 viewer is a dark, professional medical workstation organized as a
four-panel MPR grid with synchronized navigation.

## Layout

```
┌─────────────────────────────────────────────────────────┐
│ Top bar: logo · study breadcrumb · status · controls   │
├────┬────────────────────────────────────────────────────┤
│    │  ┌───────────────┬───────────────┐                │
│    │  │    AXIAL      │   SAGITTAL    │                │
│ L  │  ├───────────────┼───────────────┤                │
│ E  │  │   CORONAL     │      3D       │                │
│ F  │  └───────────────┴───────────────┘                │
│ T  ├────────────────────────────────────────────────────┤
│    │  Info bar: slice · WW · WL · X · Y · Z · HU      │
└────┴────────────────────────────────────────────────────┘
```

## Component structure

```
components/medical/mpr/
  MPRWorkspace.tsx       # 4-panel grid + state orchestration
  PlaneViewer.tsx        # reusable single-plane canvas viewer
  OrientationMarkers.tsx # A/P, R/L, S/I labels per plane
  ViewerToolbar.tsx      # left tool rail (select/pan/zoom/WL/measure)
  ViewerInfoBar.tsx      # bottom status bar
```

## State management

Centralized in a Zustand store (`lib/viewer-store.ts`) with a single source of
truth for:

- slice indices per plane
- crosshair (world mm)
- window width / level
- 3D flags (opacity, axes, grid, wireframe, camera mode, clipping)
- MPR plane visibility
- interaction mode

## Synchronization

The three slice indices (`axialSlice`, `coronalSlice`, `sagittalSlice`) are the
three coordinates of a single voxel cell. The crosshair overlay in each 2D plane
is derived from the *other two* axes:

- Axial viewer shows a marker at `(sagittalSlice, coronalSlice)` normalized.
- Coronal viewer shows `(sagittalSlice, axialSlice)`.
- Sagittal viewer shows `(coronalSlice, axialSlice)`.

This keeps the three orthogonal views coherent without duplicate state.

## Data fetching (TanStack Query)

- `useVolumeInfo` fetches volume metadata once (cached).
- `useMprSlice` fetches a windowed slice per `(plane, index, width, level)`,
  cached so scrolling back does not refetch.
- `useCrosshair` maps the current world crosshair to a voxel index + HU on
  demand.

Large volumes are never sent to the client in full — only the windowed 8-bit
PNG of the currently visible slice for each plane.
