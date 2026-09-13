"use client";

import { useState } from "react";

import { useReconstruction } from "@/hooks/useReconstruction";
import { IconCube, IconSpinner } from "@/components/ui/icons";

interface Props {
  studyId: number;
}

export function ReconstructionPanel({ studyId }: Props) {
  const { reconstruct, job } = useReconstruction(studyId);
  const [threshold, setThreshold] = useState(300);
  const [removeSmall, setRemoveSmall] = useState(true);

  const onSubmit = () => {
    reconstruct.mutate({
      threshold_hu: threshold,
      remove_small_components: removeSmall,
      method: "marching_cubes",
    });
  };

  const running = job?.data?.status === "queued" || job?.data?.status === "processing";
  const progress = job?.data?.progress ?? 0;

  return (
    <div className="space-y-4">
      <div>
        <div className="mb-1 flex items-center justify-between">
          <label className="text-xs font-medium text-slate-400">Bone threshold</label>
          <span className="font-mono text-xs text-slate-200">{threshold} HU</span>
        </div>
        <input
          type="range"
          min={-200}
          max={1500}
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
          className="slider"
          aria-label="Reconstruction threshold"
        />
        <p className="mt-1.5 text-xs text-slate-500">Voxels ≥ threshold form the bone mask.</p>
      </div>

      <label className="flex cursor-pointer items-center gap-2 text-xs text-slate-300">
        <input
          type="checkbox"
          checked={removeSmall}
          onChange={(e) => setRemoveSmall(e.target.checked)}
          className="h-3.5 w-3.5 rounded border-slate-600 bg-slate-800 text-brand-500 focus:ring-brand-500"
        />
        Remove small components
      </label>

      {running && (
        <div>
          <div className="mb-1 flex items-center justify-between">
            <span className="text-xs font-medium text-slate-300">
              {job?.data?.message ?? "Processing…"}
            </span>
            <span className="font-mono text-xs text-slate-400">
              {Math.round(progress * 100)}%
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-brand-500 transition-all"
              style={{ width: `${Math.round(progress * 100)}%` }}
            />
          </div>
        </div>
      )}

      {job?.data?.status === "completed" && (
        <p className="rounded-md bg-emerald-500/10 px-3 py-2 text-xs font-medium text-emerald-400">
          Reconstruction complete.
        </p>
      )}
      {job?.data?.status === "failed" && (
        <p className="rounded-md bg-red-500/10 px-3 py-2 text-xs font-medium text-red-400">
          {job.data.error ?? "Reconstruction failed."}
        </p>
      )}

      <button onClick={onSubmit} disabled={running} className="btn-primary w-full px-4 py-2">
        {running ? (
          <>
            <IconSpinner className="h-4 w-4" />
            Reconstructing…
          </>
        ) : (
          <>
            <IconCube className="h-4 w-4" />
            Generate bone surface
          </>
        )}
      </button>
    </div>
  );
}
