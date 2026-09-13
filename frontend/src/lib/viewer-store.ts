"use client";

import { create } from "zustand";

import type { PlaneName } from "@/types/medical";

export type InteractionMode =
  | "select" // crosshair navigation
  | "pan"
  | "zoom"
  | "window_level"
  | "measure"
  | "clip";

export type CameraMode = "perspective" | "orthographic";

export interface Crosshair {
  x: number;
  y: number;
  z: number;
}

interface ViewerState {
  // Slice indices per plane (voxel index along each axis).
  axialSlice: number;
  coronalSlice: number;
  sagittalSlice: number;

  // Crosshair location in physical mm (world coordinates).
  crosshair: Crosshair;

  // Window/level.
  windowWidth: number;
  windowLevel: number;

  // 3D rendering.
  modelOpacity: number;
  showAxes: boolean;
  showGrid: boolean;
  wireframe: boolean;
  cameraMode: CameraMode;
  clipping: { x: number | null; y: number | null; z: number | null };

  // MPR plane visualization in 3D.
  showAxialPlane: boolean;
  showCoronalPlane: boolean;
  showSagittalPlane: boolean;

  // Interaction.
  interactionMode: InteractionMode;
  activeViewer: PlaneName | "3d";

  // Actions.
  setAxialSlice: (n: number) => void;
  setCoronalSlice: (n: number) => void;
  setSagittalSlice: (n: number) => void;
  setCrosshair: (c: Crosshair) => void;
  setWindowWidth: (n: number) => void;
  setWindowLevel: (n: number) => void;
  setModelOpacity: (n: number) => void;
  toggleAxes: () => void;
  toggleGrid: () => void;
  toggleWireframe: () => void;
  setCameraMode: (m: CameraMode) => void;
  setClipping: (axis: "x" | "y" | "z", value: number | null) => void;
  togglePlane: (p: PlaneName) => void;
  setInteractionMode: (m: InteractionMode) => void;
  setActiveViewer: (v: PlaneName | "3d") => void;
  resetView: () => void;
}

export const useViewerStore = create<ViewerState>((set) => ({
  axialSlice: 0,
  coronalSlice: 0,
  sagittalSlice: 0,

  crosshair: { x: 0, y: 0, z: 0 },

  windowWidth: 400,
  windowLevel: 40,

  modelOpacity: 1.0,
  showAxes: true,
  showGrid: true,
  wireframe: false,
  cameraMode: "perspective",
  clipping: { x: null, y: null, z: null },

  showAxialPlane: false,
  showCoronalPlane: false,
  showSagittalPlane: false,

  interactionMode: "select",
  activeViewer: "axial",

  setAxialSlice: (n) => set({ axialSlice: n }),
  setCoronalSlice: (n) => set({ coronalSlice: n }),
  setSagittalSlice: (n) => set({ sagittalSlice: n }),
  setCrosshair: (c) => set({ crosshair: c }),
  setWindowWidth: (n) => set({ windowWidth: n }),
  setWindowLevel: (n) => set({ windowLevel: n }),
  setModelOpacity: (n) => set({ modelOpacity: n }),
  toggleAxes: () => set((s) => ({ showAxes: !s.showAxes })),
  toggleGrid: () => set((s) => ({ showGrid: !s.showGrid })),
  toggleWireframe: () => set((s) => ({ wireframe: !s.wireframe })),
  setCameraMode: (m) => set({ cameraMode: m }),
  setClipping: (axis, value) =>
    set((s) => ({ clipping: { ...s.clipping, [axis]: value } })),
  togglePlane: (p) =>
    set((s) => {
      if (p === "axial") return { showAxialPlane: !s.showAxialPlane };
      if (p === "coronal") return { showCoronalPlane: !s.showCoronalPlane };
      return { showSagittalPlane: !s.showSagittalPlane };
    }),
  setInteractionMode: (m) => set({ interactionMode: m }),
  setActiveViewer: (v) => set({ activeViewer: v }),
  resetView: () =>
    set({
      axialSlice: 0,
      coronalSlice: 0,
      sagittalSlice: 0,
      crosshair: { x: 0, y: 0, z: 0 },
      modelOpacity: 1.0,
      cameraMode: "perspective",
      clipping: { x: null, y: null, z: null },
      wireframe: false,
      interactionMode: "select",
    }),
}));
