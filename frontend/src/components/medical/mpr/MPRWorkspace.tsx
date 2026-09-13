"use client";

import { useCallback, useEffect, useMemo } from "react";

import { PlaneViewer } from "./PlaneViewer";
import { ViewerInfoBar } from "./ViewerInfoBar";
import { ViewerToolbar } from "./ViewerToolbar";
import { ThreeDViewer } from "@/components/medical/ThreeDViewer";
import { useMprSlice, useVolumeInfo } from "@/hooks/useMpr";
import { useViewerStore } from "@/lib/viewer-store";
import type { Model } from "@/types/medical";

interface Props {
  studyId: number;
  model: Model | undefined;
  markers: [number, number, number][];
  onAddMarker: (point: [number, number, number]) => void;
}

/**
 * The four-panel MPR medical workstation: axial, sagittal, coronal, and 3D
 * views, all synchronized to the same physical crosshair location.
 */
export function MPRWorkspace({ studyId, model, markers, onAddMarker }: Props) {
  const axialSlice = useViewerStore((s) => s.axialSlice);
  const coronalSlice = useViewerStore((s) => s.coronalSlice);
  const sagittalSlice = useViewerStore((s) => s.sagittalSlice);
  const setAxialSlice = useViewerStore((s) => s.setAxialSlice);
  const setCoronalSlice = useViewerStore((s) => s.setCoronalSlice);
  const setSagittalSlice = useViewerStore((s) => s.setSagittalSlice);
  const windowWidth = useViewerStore((s) => s.windowWidth);
  const windowLevel = useViewerStore((s) => s.windowLevel);
  const setWindowWidth = useViewerStore((s) => s.setWindowWidth);
  const setWindowLevel = useViewerStore((s) => s.setWindowLevel);
  const interactionMode = useViewerStore((s) => s.interactionMode);
  const activeViewer = useViewerStore((s) => s.activeViewer);
  const setActiveViewer = useViewerStore((s) => s.setActiveViewer);
  const crosshair = useViewerStore((s) => s.crosshair);
  const setCrosshair = useViewerStore((s) => s.setCrosshair);

  const { data: volumeInfo } = useVolumeInfo(studyId);

  const axial = useMprSlice(studyId, "axial", axialSlice, windowWidth, windowLevel);
  const coronal = useMprSlice(studyId, "coronal", coronalSlice, windowWidth, windowLevel);
  const sagittal = useMprSlice(studyId, "sagittal", sagittalSlice, windowWidth, windowLevel);

  // Initial slice positions to centers when volume loads.
  useEffect(() => {
    if (volumeInfo) {
      const [depth, height, width] = volumeInfo.shape;
      if (axialSlice === 0 && depth > 1) setAxialSlice(Math.floor(depth / 2));
      if (coronalSlice === 0 && height > 1) setCoronalSlice(Math.floor(height / 2));
      if (sagittalSlice === 0 && width > 1) setSagittalSlice(Math.floor(width / 2));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [volumeInfo]);

  // Compute crosshair overlay positions (normalized 0..1) per plane.
  // The crosshair (world mm) maps to a voxel index; within each plane's image,
  // we show a marker at the fractional position of the other axes.
  const normalizedCrosshair = useMemo(() => {
    if (!volumeInfo) return { axial: null, coronal: null, sagittal: null } as const;
    const [depth, height, width] = volumeInfo.shape;
    return {
      // axial image: rows=y (height), cols=x (width)
      axial: {
        x: sagittalSlice / (width - 1 || 1),
        y: coronalSlice / (height - 1 || 1),
      },
      // coronal image: rows=z (depth), cols=x (width)
      coronal: {
        x: sagittalSlice / (width - 1 || 1),
        y: axialSlice / (depth - 1 || 1),
      },
      // sagittal image: rows=z (depth), cols=y (height)
      sagittal: {
        x: coronalSlice / (height - 1 || 1),
        y: axialSlice / (depth - 1 || 1),
      },
    };
  }, [volumeInfo, sagittalSlice, coronalSlice, axialSlice]);

  // HU display: use crosshair coordinate lookup is expensive; approximate from
  // axial slice is not trivial without a fetch. We show nothing here — the info
  // bar HU is populated by the coordinates endpoint when crosshair moves.
  const hu = null;

  return (
    <div className="flex h-full flex-col bg-slate-925">
      {/* Main content: left toolbar + 4-panel grid */}
      <div className="flex flex-1 overflow-hidden">
        <ViewerToolbar />

        <div className="grid flex-1 grid-cols-2 grid-rows-2 gap-px bg-slate-800 p-px">
          {/* AXIAL (top-left) */}
          <div className="bg-slate-925">
            <PlaneViewer
              plane="axial"
              slice={axial.data}
              index={axialSlice}
              total={axial.data?.total ?? 0}
              onIndexChange={setAxialSlice}
              active={activeViewer === "axial"}
              onActivate={() => setActiveViewer("axial")}
              interactionMode={interactionMode}
              onWindowLevel={(w, l) => {
                setWindowWidth(w);
                setWindowLevel(l);
              }}
              windowWidth={windowWidth}
              windowLevel={windowLevel}
              crosshair={normalizedCrosshair.axial}
            />
          </div>

          {/* SAGITTAL (top-right) */}
          <div className="bg-slate-925">
            <PlaneViewer
              plane="sagittal"
              slice={sagittal.data}
              index={sagittalSlice}
              total={sagittal.data?.total ?? 0}
              onIndexChange={setSagittalSlice}
              active={activeViewer === "sagittal"}
              onActivate={() => setActiveViewer("sagittal")}
              interactionMode={interactionMode}
              onWindowLevel={(w, l) => {
                setWindowWidth(w);
                setWindowLevel(l);
              }}
              windowWidth={windowWidth}
              windowLevel={windowLevel}
              crosshair={normalizedCrosshair.sagittal}
            />
          </div>

          {/* CORONAL (bottom-left) */}
          <div className="bg-slate-925">
            <PlaneViewer
              plane="coronal"
              slice={coronal.data}
              index={coronalSlice}
              total={coronal.data?.total ?? 0}
              onIndexChange={setCoronalSlice}
              active={activeViewer === "coronal"}
              onActivate={() => setActiveViewer("coronal")}
              interactionMode={interactionMode}
              onWindowLevel={(w, l) => {
                setWindowWidth(w);
                setWindowLevel(l);
              }}
              windowWidth={windowWidth}
              windowLevel={windowLevel}
              crosshair={normalizedCrosshair.coronal}
            />
          </div>

          {/* 3D (bottom-right) */}
          <div className="bg-slate-925">
            {model ? (
              <ThreeDViewer
                model={model}
                markers={markers}
                onAddMarker={onAddMarker}
                volumeShape={volumeInfo?.shape}
                spacing={volumeInfo?.spacing}
              />
            ) : (
              <div className="flex h-full flex-col items-center justify-center text-center text-slate-500">
                <p className="text-sm font-medium text-slate-400">3D Model</p>
                <p className="mt-1 text-xs">Generate a bone surface to load the model.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom info bar */}
      <ViewerInfoBar
        axialSlice={axialSlice}
        axialTotal={axial.data?.total ?? 0}
        hu={hu}
      />
    </div>
  );
}
