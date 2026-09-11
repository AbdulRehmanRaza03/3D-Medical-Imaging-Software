"use client";

import { IconSliders } from "@/components/ui/icons";

interface Props {
  width: number;
  level: number;
  onWidthChange: (w: number) => void;
  onLevelChange: (l: number) => void;
}

const PRESETS: [string, number, number][] = [
  ["Bone", 1800, 400],
  ["Soft tissue", 400, 40],
  ["Lung", 1500, -600],
];

export function WindowLevelControls({ width, level, onWidthChange, onLevelChange }: Props) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-1.5">
        {PRESETS.map(([label, w, l]) => (
          <button
            key={label}
            onClick={() => {
              onWidthChange(w);
              onLevelChange(l);
            }}
            className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 shadow-sm transition hover:border-brand-300 hover:text-brand-600"
          >
            {label}
          </button>
        ))}
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between">
          <label className="text-xs font-medium text-slate-500">Window width</label>
          <span className="font-mono text-xs text-slate-600">{Math.round(width)}</span>
        </div>
        <input
          type="range"
          min={1}
          max={4000}
          value={width}
          onChange={(e) => onWidthChange(Number(e.target.value))}
          className="slider"
          aria-label="Window width"
        />
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between">
          <label className="text-xs font-medium text-slate-500">Window level</label>
          <span className="font-mono text-xs text-slate-600">{Math.round(level)}</span>
        </div>
        <input
          type="range"
          min={-1500}
          max={3000}
          value={level}
          onChange={(e) => onLevelChange(Number(e.target.value))}
          className="slider"
          aria-label="Window level"
        />
      </div>
    </div>
  );
}
