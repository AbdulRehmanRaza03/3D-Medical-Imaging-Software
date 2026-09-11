"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api/client";

/** 2D slice viewer state: current slice, window/level. */
export function useSliceViewer(
  studyId: number | null,
  index: number,
  width?: number,
  level?: number,
) {
  const slice = useQuery({
    queryKey: ["slice", studyId, index, width, level],
    queryFn: () => api.getSlice(studyId as number, index, width, level),
    enabled: studyId != null,
  });

  return { slice };
}
