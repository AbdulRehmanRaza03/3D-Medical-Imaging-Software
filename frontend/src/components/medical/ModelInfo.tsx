"use client";

import type { Metadata, Model } from "@/types/medical";

function Row({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value == null || value === "") return null;
  return (
    <div className="flex items-baseline justify-between gap-3 py-1">
      <span className="shrink-0 text-xs text-slate-500">{label}</span>
      <span className="truncate text-right font-mono text-xs text-slate-200">{value}</span>
    </div>
  );
}

interface Props {
  metadata: Metadata | undefined;
  model: Model | undefined;
}

export function ModelInfo({ metadata, model }: Props) {
  const spacing = metadata?.pixel_spacing;
  const spacingStr = spacing
    ? `${spacing[0]?.toFixed(2)} × ${spacing[1]?.toFixed(2)} × ${(metadata.slice_spacing ?? 0).toFixed(2)}`
    : undefined;

  const physical = model?.physical_size;
  const physicalStr = physical
    ? `${physical[0]?.toFixed(1)} × ${physical[1]?.toFixed(1)} × ${physical[2]?.toFixed(1)} mm`
    : undefined;

  return (
    <div className="space-y-4">
      <div>
        <h4 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Study
        </h4>
        <div className="divide-y divide-slate-800">
          <Row label="Modality" value={metadata?.modality} />
          <Row label="Slices" value={metadata?.slice_count} />
          <Row label="Dimensions" value={metadata ? `${metadata.rows} × ${metadata.columns}` : undefined} />
          <Row label="Voxel spacing" value={spacingStr} />
          <Row label="Study date" value={metadata?.study_date} />
          <Row label="Description" value={metadata?.series_description} />
        </div>
      </div>

      {model && (
        <div>
          <h4 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Model
          </h4>
          <div className="divide-y divide-slate-800">
            <Row label="Method" value={model.method.replace(/_/g, " ")} />
            <Row label="Threshold" value={`${model.threshold_hu} HU`} />
            <Row label="Vertices" value={model.vertices.toLocaleString()} />
            <Row label="Triangles" value={model.triangles.toLocaleString()} />
            <Row label="Physical size" value={physicalStr} />
          </div>
        </div>
      )}
    </div>
  );
}
