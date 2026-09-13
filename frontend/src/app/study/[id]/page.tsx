"use client";

import { useParams } from "next/navigation";
import { useState } from "react";

import { MPRWorkspace } from "@/components/medical/mpr/MPRWorkspace";
import { ReconstructionPanel } from "@/components/medical/ReconstructionPanel";
import { SegmentationPanel } from "@/components/medical/SegmentationPanel";
import { WindowLevelControls } from "@/components/medical/WindowLevelControls";
import { ExportPanel } from "@/components/medical/ExportPanel";
import { ModelInfo } from "@/components/medical/ModelInfo";
import { MeasurementTool } from "@/components/medical/MeasurementTool";
import { StatusBadge } from "@/components/ui/Badge";
import { IconLogo, IconSliders } from "@/components/ui/icons";
import { useMetadata, useStudy } from "@/hooks/useStudy";
import { useReconstruction } from "@/hooks/useReconstruction";
import { useViewerStore } from "@/lib/viewer-store";

export default function StudyPage() {
  const params = useParams<{ id: string }>();
  const studyId = Number(params.id);
  const [showPanel, setShowPanel] = useState(true);
  const [markers, setMarkers] = useState<[number, number, number][]>([]);

  const { data: study } = useStudy(studyId);
  const { data: metadata } = useMetadata(studyId);
  const { models } = useReconstruction(studyId);

  const model = models.data?.models?.[0];

  const windowWidth = useViewerStore((s) => s.windowWidth);
  const windowLevel = useViewerStore((s) => s.windowLevel);
  const setWindowWidth = useViewerStore((s) => s.setWindowWidth);
  const setWindowLevel = useViewerStore((s) => s.setWindowLevel);

  const addMarker = (point: [number, number, number]) => setMarkers((m) => [...m, point]);
  const clearMarkers = () => setMarkers([]);

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      {/* Top bar */}
      <header className="flex h-12 shrink-0 items-center gap-4 border-b border-slate-800 bg-slate-925 px-4">
        <a href="/" className="flex items-center gap-2" title="Back to dashboard">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-600 text-white">
            <IconLogo className="h-4 w-4" />
          </span>
          <span className="text-sm font-semibold tracking-tight">OrthoVision AI</span>
        </a>

        <span className="text-slate-600">/</span>
        <span className="truncate text-sm text-slate-300">{study?.name ?? "Study"}</span>
        {study && <StatusBadge status={study.status} />}

        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setShowPanel((v) => !v)}
            className={`flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs font-medium transition ${
              showPanel
                ? "border-brand-500/60 bg-brand-500/15 text-brand-300"
                : "border-slate-700 text-slate-300 hover:bg-slate-800"
            }`}
          >
            <IconSliders className="h-3.5 w-3.5" />
            Controls
          </button>
        </div>
      </header>

      {/* Main body */}
      <div className="flex min-h-0 flex-1">
        {/* Viewer workspace (full-bleed) */}
        <div className="min-w-0 flex-1">
          <MPRWorkspace
            studyId={studyId}
            model={model}
            markers={markers}
            onAddMarker={addMarker}
          />
        </div>

        {/* Control panel */}
        {showPanel && (
          <aside className="w-72 shrink-0 overflow-y-auto border-l border-slate-800 bg-slate-925">
            <div className="space-y-5 p-4">
              <section>
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Window / Level
                </h3>
                <WindowLevelControls
                  width={windowWidth}
                  level={windowLevel}
                  onWidthChange={setWindowWidth}
                  onLevelChange={setWindowLevel}
                />
              </section>

              <section>
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Reconstruction
                </h3>
                <ReconstructionPanel studyId={studyId} />
              </section>

              <section>
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  AI Segmentation
                </h3>
                <SegmentationPanel studyId={studyId} />
              </section>

              <section>
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Measurements
                </h3>
                {model ? (
                  <MeasurementTool
                    modelId={model.id}
                    markers={markers}
                    onAddMarker={addMarker}
                    onClear={clearMarkers}
                  />
                ) : (
                  <p className="text-xs text-slate-500">Generate a model first.</p>
                )}
              </section>

              <section>
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Model
                </h3>
                {model ? (
                  <div className="space-y-4">
                    <ModelInfo metadata={metadata} model={model} />
                    <ExportPanel modelId={model.id} />
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No model yet.</p>
                )}
              </section>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
