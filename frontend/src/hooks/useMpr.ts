"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api/client";
import { useViewerStore } from "@/lib/viewer-store";
import type { PlaneName } from "@/types/medical";

/** Loads volume metadata once per study (cached). */
export function useVolumeInfo(studyId: number | null) {
  return useQuery({
    queryKey: ["volume", studyId],
    queryFn: () => api.getVolumeInfo(studyId as number),
    enabled: studyId != null,
  });
}

/** Loads a single MPR plane slice (cached per plane+index+window/level). */
export function useMprSlice(
  studyId: number | null,
  plane: PlaneName,
  index: number,
  width: number,
  level: number,
) {
  return useQuery({
    queryKey: ["mpr", studyId, plane, index, width, level],
    queryFn: () => api.getMprSlice(studyId as number, plane, index, width, level),
    enabled: studyId != null,
  });
}

/**
 * Given a physical crosshair point, derive the voxel indices for each plane so
 * all three orthogonal viewers remain synchronized.
 */
export function useCrosshair(studyId: number | null) {
  const crosshair = useViewerStore((s) => s.crosshair);
  return useQuery({
    queryKey: ["crosshair", studyId, crosshair.x, crosshair.y, crosshair.z],
    queryFn: () =>
      api.getCoordinates(studyId as number, crosshair.x, crosshair.y, crosshair.z),
    enabled: studyId != null,
  });
}
