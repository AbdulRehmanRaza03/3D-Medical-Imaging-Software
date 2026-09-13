import { describe, it, expect, beforeEach } from "vitest";

import { useViewerStore } from "@/lib/viewer-store";

describe("viewer store", () => {
  beforeEach(() => {
    useViewerStore.getState().resetView();
  });

  it("updates slice indices", () => {
    useViewerStore.getState().setAxialSlice(42);
    expect(useViewerStore.getState().axialSlice).toBe(42);

    useViewerStore.getState().setCoronalSlice(120);
    expect(useViewerStore.getState().coronalSlice).toBe(120);

    useViewerStore.getState().setSagittalSlice(7);
    expect(useViewerStore.getState().sagittalSlice).toBe(7);
  });

  it("updates crosshair", () => {
    useViewerStore.getState().setCrosshair({ x: 10, y: -20, z: 30 });
    expect(useViewerStore.getState().crosshair).toEqual({ x: 10, y: -20, z: 30 });
  });

  it("updates window/level", () => {
    useViewerStore.getState().setWindowWidth(1500);
    useViewerStore.getState().setWindowLevel(300);
    expect(useViewerStore.getState().windowWidth).toBe(1500);
    expect(useViewerStore.getState().windowLevel).toBe(300);
  });

  it("toggles 3D flags", () => {
    const s = useViewerStore.getState();
    expect(s.showAxes).toBe(true);
    s.toggleAxes();
    expect(useViewerStore.getState().showAxes).toBe(false);

    expect(useViewerStore.getState().showGrid).toBe(true);
    useViewerStore.getState().toggleGrid();
    expect(useViewerStore.getState().showGrid).toBe(false);

    expect(useViewerStore.getState().wireframe).toBe(false);
    useViewerStore.getState().toggleWireframe();
    expect(useViewerStore.getState().wireframe).toBe(true);
  });

  it("updates model opacity", () => {
    useViewerStore.getState().setModelOpacity(0.6);
    expect(useViewerStore.getState().modelOpacity).toBe(0.6);
  });

  it("toggles MPR planes", () => {
    expect(useViewerStore.getState().showAxialPlane).toBe(false);
    useViewerStore.getState().togglePlane("axial");
    expect(useViewerStore.getState().showAxialPlane).toBe(true);

    useViewerStore.getState().togglePlane("coronal");
    expect(useViewerStore.getState().showCoronalPlane).toBe(true);

    useViewerStore.getState().togglePlane("sagittal");
    expect(useViewerStore.getState().showSagittalPlane).toBe(true);
  });

  it("changes interaction mode", () => {
    useViewerStore.getState().setInteractionMode("window_level");
    expect(useViewerStore.getState().interactionMode).toBe("window_level");
    useViewerStore.getState().setInteractionMode("measure");
    expect(useViewerStore.getState().interactionMode).toBe("measure");
  });

  it("reset restores defaults", () => {
    useViewerStore.getState().setAxialSlice(99);
    useViewerStore.getState().setModelOpacity(0.2);
    useViewerStore.getState().toggleWireframe();
    useViewerStore.getState().resetView();
    const s = useViewerStore.getState();
    expect(s.axialSlice).toBe(0);
    expect(s.modelOpacity).toBe(1.0);
    expect(s.wireframe).toBe(false);
  });
});
