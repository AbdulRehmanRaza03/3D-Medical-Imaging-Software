"use client";

import type { PlaneName } from "@/types/medical";

/**
 * Anatomical orientation markers for each MPR plane.
 *
 * Labels are derived from the plane definition, not hardcoded to a single
 * scanner. For the standard near-axial CT convention used in this dataset
 * (row→x, col→y, slice→z), the markers are:
 *
 *   axial    : R/L (left-right), A/P (anterior-posterior)
 *   coronal  : R/L, S/I (superior-inferior)
 *   sagittal : A/P, S/I
 */
const MARKERS: Record<PlaneName, { top: string; bottom: string; left: string; right: string }> = {
  axial: { top: "A", bottom: "P", left: "R", right: "L" },
  coronal: { top: "S", bottom: "I", left: "R", right: "L" },
  sagittal: { top: "S", bottom: "I", left: "A", right: "P" },
};

export function OrientationMarkers({ plane }: { plane: PlaneName }) {
  const m = MARKERS[plane];
  const cls = "pointer-events-none absolute font-mono text-[10px] font-medium tracking-widest text-slate-600 select-none";
  return (
    <>
      <span className={`${cls} left-1/2 top-2 -translate-x-1/2`}>{m.top}</span>
      <span className={`${cls} bottom-2 left-1/2 -translate-x-1/2`}>{m.bottom}</span>
      <span className={`${cls} left-2 top-1/2 -translate-y-1/2`}>{m.left}</span>
      <span className={`${cls} right-2 top-1/2 -translate-y-1/2`}>{m.right}</span>
    </>
  );
}
