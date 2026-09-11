"use client";

import { useParams } from "next/navigation";
import { useState } from "react";

import { ExportPanel } from "@/components/medical/ExportPanel";
import { MeasurementTool } from "@/components/medical/MeasurementTool";
import { ModelInfo } from "@/components/medical/ModelInfo";
import { ReconstructionPanel } from "@/components/medical/ReconstructionPanel";
import { SliceViewer } from "@/components/medical/SliceViewer";
import { ThreeDViewer } from "@/components/medical/ThreeDViewer";
import { WindowLevelControls } from "@/components/medical/WindowLevelControls";
import { AppShell } from "@/components/ui/AppShell";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { useMetadata, useStudy } from "@/hooks/useStudy";
import { useSliceViewer } from "@/hooks/useSliceViewer";
import { useReconstruction } from "@/hooks/useReconstruction";

export default function StudyPage() {
  const params = useParams<{ id: string }>();
  const studyId = Number(params.id);
  const [sliceIndex, setSliceIndex] = useState(0);
  const [width, setWidth] = useState(400);
  const [level, setLevel] = useState(40);
  const [markers, setMarkers] = useState<[number, number, number][]>([]);

  const { data: study } = useStudy(studyId);
  const { data: metadata } = useMetadata(studyId);
  const { slice } = useSliceViewer(studyId, sliceIndex, width, level);
  const { models } = useReconstruction(studyId);

  const model = models.data?.models?.[0];

  const addMarker = (point: [number, number, number]) => {
    setMarkers((m) => [...m, point]);
  };
  const clearMarkers = () => setMarkers([]);

  return (
    <AppShell>
      {/* Header bar */}
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-3 px-5 py-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2.5">
              <h2 className="truncate text-base font-semibold text-slate-900">
                {study?.name ?? "Study"}
              </h2>
              {study && <StatusBadge status={study.status} />}
            </div>
            <p className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
              <span className="font-mono">{study?.study_uid?.slice(0, 14)}…</span>
              <span>·</span>
              <span>{study?.modality ?? "CT"}</span>
              <span>·</span>
              <span>{study?.slice_count ?? 0} slices</span>
            </p>
          </div>
          <div className="hidden shrink-0 items-center gap-2 md:flex">
            <Badge tone="blue">Medical Viewer</Badge>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-[1600px] px-5 py-4">
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
          {/* Viewers */}
          <div className="xl:col-span-9 space-y-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {/* 2D viewer */}
              <Card className="overflow-hidden !p-0 shadow-panel">
                <div className="viewer-dark h-[440px]">
                  <SliceViewer
                    slice={slice.data}
                    index={sliceIndex}
                    total={slice.data?.total ?? 0}
                    onIndexChange={setSliceIndex}
                  />
                </div>
              </Card>

              {/* 3D viewer */}
              <Card className="overflow-hidden !p-0 shadow-panel">
                <div className="viewer-dark h-[440px]">
                  {model ? (
                    <ThreeDViewer model={model} markers={markers} onAddMarker={addMarker} />
                  ) : (
                    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
                      <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 text-slate-400">
                        <span className="text-lg">🧊</span>
                      </span>
                      <p className="mt-3 text-sm font-medium text-slate-300">
                        No model generated yet
                      </p>
                      <p className="mt-1 max-w-xs text-xs text-slate-500">
                        Use the reconstruction panel to generate a bone surface.
                      </p>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </div>

          {/* Controls sidebar */}
          <div className="xl:col-span-3 space-y-4">
            <Card>
              <CardHeader title="Window / Level" />
              <CardBody>
                <WindowLevelControls
                  width={width}
                  level={level}
                  onWidthChange={setWidth}
                  onLevelChange={setLevel}
                />
              </CardBody>
            </Card>

            <Card>
              <CardHeader title="Reconstruction" />
              <CardBody>
                <ReconstructionPanel studyId={studyId} />
              </CardBody>
            </Card>

            <Card>
              <CardHeader title="Measurements" />
              <CardBody>
                {model ? (
                  <MeasurementTool
                    modelId={model.id}
                    markers={markers}
                    onAddMarker={addMarker}
                    onClear={clearMarkers}
                  />
                ) : (
                  <p className="text-xs text-slate-400">Generate a model first.</p>
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader title="Model Info" />
              <CardBody>
                {model && (
                  <div className="mb-4 border-b border-slate-100 pb-4">
                    <ExportPanel modelId={model.id} />
                  </div>
                )}
                <ModelInfo metadata={metadata} model={model} />
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
