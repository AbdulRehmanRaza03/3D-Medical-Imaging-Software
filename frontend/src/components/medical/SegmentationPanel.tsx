"use client";

import { useState } from "react";

import { useSegmentation } from "@/hooks/useSegmentation";
import { IconSpinner } from "@/components/ui/icons";
import type { SegmentationModelInfo, SegmentationResult } from "@/types/medical";

function ModelSelect({
  models,
  value,
  onChange,
}: {
  models: SegmentationModelInfo[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-brand-500 focus:outline-none"
    >
      {models.map((m) => (
        <option key={m.id} value={m.id}>
          {m.name} v{m.version}
        </option>
      ))}
    </select>
  );
}

function ResultRow({ result }: { result: SegmentationResult }) {
  const label = result.labels.find((l) => l.id === 1);
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-300">
          {result.model_id.replace(/_/g, " ")}
        </span>
        <span className="text-[10px] uppercase tracking-wide text-emerald-400">
          {result.status}
        </span>
      </div>
      {label && label.voxel_count > 0 && (
        <div className="mt-1.5 space-y-0.5">
          <p className="text-xs text-slate-400">
            <span className="text-slate-300">{label.name}</span> ·{" "}
            {label.voxel_count.toLocaleString()} voxels
          </p>
          <p className="text-xs text-slate-400">
            Volume <span className="font-mono text-slate-200">{label.volume_cm3} cm³</span>
          </p>
        </div>
      )}
      <p className="mt-1 text-[10px] text-slate-500">
        {new Date(result.created_at + "Z").toLocaleString()}
      </p>
    </div>
  );
}

export function SegmentationPanel({ studyId }: { studyId: number }) {
  const { models, results, run, job } = useSegmentation(studyId);
  const [selectedModel, setSelectedModel] = useState<string>("bone_1");

  const modelList = models.data ?? [];

  // Update selection once models load.
  if (modelList.length > 0 && !modelList.some((m) => m.id === selectedModel)) {
    setSelectedModel(modelList[0].id);
  }

  const selected = modelList.find((m) => m.id === selectedModel);
  const checkpointReady = selected?.checkpoint_available ?? false;

  const running = job?.data?.status === "queued" || job?.data?.status === "processing";

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-400">Model</label>
        {modelList.length > 0 ? (
          <ModelSelect models={modelList} value={selectedModel} onChange={setSelectedModel} />
        ) : (
          <p className="text-xs text-slate-500">Loading models…</p>
        )}
      </div>

      {selected && (
        <div className="rounded-md bg-slate-800/50 px-3 py-2 text-xs text-slate-400">
          <p>
            <span className="text-slate-300">{selected.name}</span> · v{selected.version}
          </p>
          <p className="mt-0.5">Labels: {selected.labels.join(", ")}</p>
          <p className="mt-0.5">Framework: {selected.framework}</p>
          {!checkpointReady && (
            <p className="mt-1 font-medium text-amber-400">
              Model checkpoint required
            </p>
          )}
        </div>
      )}

      <button
        onClick={() => run.mutate(selectedModel)}
        disabled={running || run.isPending || !checkpointReady}
        className="btn-primary w-full px-4 py-2"
      >
        {running || run.isPending ? (
          <>
            <IconSpinner className="h-4 w-4" />
            Running…
          </>
        ) : (
          "Run Segmentation"
        )}
      </button>

      {running && (
        <div>
          <div className="mb-1 flex items-center justify-between">
            <span className="text-xs text-slate-300">{job?.data?.message ?? "Processing…"}</span>
            <span className="font-mono text-xs text-slate-400">
              {Math.round((job?.data?.progress ?? 0) * 100)}%
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-brand-500 transition-all"
              style={{ width: `${Math.round((job?.data?.progress ?? 0) * 100)}%` }}
            />
          </div>
        </div>
      )}

      {job?.data?.status === "failed" && (
        <p className="rounded-md bg-red-500/10 px-3 py-2 text-xs font-medium text-red-400">
          {job.data.error ?? "Segmentation failed."}
        </p>
      )}

      {/* Previous results */}
      {results.data && results.data.results.length > 0 && (
        <div>
          <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Results
          </h4>
          <div className="space-y-2">
            {results.data.results.map((r) => (
              <ResultRow key={r.id} result={r} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
