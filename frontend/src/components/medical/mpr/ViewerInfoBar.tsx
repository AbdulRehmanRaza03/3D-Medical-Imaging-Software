"use client";

import { useViewerStore } from "@/lib/viewer-store";

interface Props {
  axialSlice: number;
  axialTotal: number;
  hu?: number | null;
}

/**
 * Global viewer information bar showing slice, window/level, zoom, world
 * coordinates, and voxel intensity (HU).
 */
export function ViewerInfoBar({ axialSlice, axialTotal, hu }: Props) {
  const windowWidth = useViewerStore((s) => s.windowWidth);
  const windowLevel = useViewerStore((s) => s.windowLevel);
  const crosshair = useViewerStore((s) => s.crosshair);

  const item = "flex items-center gap-1.5 text-[11px] text-slate-500";
  const value = "font-mono text-slate-200";

  return (
    <div className="flex items-center gap-4 border-t border-slate-800 bg-slate-925 px-3 py-1.5">
      <span className={item}>
        Slice <span className={value}>{axialSlice + 1}/{axialTotal}</span>
      </span>
      <span className="h-3 w-px bg-slate-800" />
      <span className={item}>
        WW <span className={value}>{Math.round(windowWidth)}</span>
      </span>
      <span className={item}>
        WL <span className={value}>{Math.round(windowLevel)}</span>
      </span>
      <span className="h-3 w-px bg-slate-800" />
      <span className={item}>
        X <span className={value}>{crosshair.x.toFixed(1)}</span>
      </span>
      <span className={item}>
        Y <span className={value}>{crosshair.y.toFixed(1)}</span>
      </span>
      <span className={item}>
        Z <span className={value}>{crosshair.z.toFixed(1)}</span>
      </span>
      {hu != null && (
        <>
          <span className="h-3 w-px bg-slate-800" />
          <span className={item}>
            HU <span className={value}>{Math.round(hu)}</span>
          </span>
        </>
      )}
    </div>
  );
}
