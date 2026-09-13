"use client";

import { useState } from "react";

import { useMeasurements } from "@/hooks/useMeasurements";

interface Props {
  modelId: number;
  markers: [number, number, number][];
  onAddMarker: (p: [number, number, number]) => void;
  onClear: () => void;
}

export function MeasurementTool({ modelId, markers, onAddMarker, onClear }: Props) {
  const { create } = useMeasurements();
  const [mode, setMode] = useState<"distance" | "angle">("distance");
  const [result, setResult] = useState<string | null>(null);

  const needed = mode === "distance" ? 2 : 3;

  const onSubmit = async () => {
    if (markers.length < needed) return;
    const points = markers.slice(0, needed);
    const res = await create.mutateAsync({ modelId, points, type: mode });
    const m = res.measurement;
    setResult(
      mode === "distance"
        ? `Distance: ${m.value.toFixed(2)} ${m.unit}`
        : `Angle: ${m.value.toFixed(2)} °`,
    );
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-1">
        {(["distance", "angle"] as const).map((m) => (
          <button
            key={m}
            onClick={() => {
              setMode(m);
              setResult(null);
              onClear();
            }}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
              mode === m
                ? "bg-brand-600 text-white shadow-sm"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            {m === "distance" ? "Distance" : "Angle"}
          </button>
        ))}
      </div>

      <p className="text-xs text-slate-400">
        {mode === "distance" ? "Pick 2 points" : "Pick 3 points"}{" "}
        <span className="font-mono text-slate-300">
          {markers.length}/{needed}
        </span>{" "}
        selected.
      </p>

      <div className="flex items-center gap-2">
        <button
          onClick={onSubmit}
          disabled={markers.length < needed || create.isPending}
          className="btn-primary px-3 py-1.5 text-xs"
        >
          Calculate
        </button>
        <button
          onClick={onClear}
          className="rounded-md px-2 py-1.5 text-xs text-slate-400 transition hover:bg-slate-800 hover:text-slate-200"
        >
          Clear
        </button>
      </div>

      {result && (
        <p className="rounded-md bg-slate-800 px-3 py-2 font-mono text-sm font-medium text-brand-300">
          {result}
        </p>
      )}
    </div>
  );
}
