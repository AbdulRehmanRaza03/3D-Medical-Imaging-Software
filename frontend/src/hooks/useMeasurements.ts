"use client";

import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api/client";

/** Measurement submission hook. */
export function useMeasurements() {
  const create = useMutation({
    mutationFn: (args: {
      modelId: number;
      points: number[][];
      type: "distance" | "angle";
    }) => api.createMeasurement(args.modelId, args.points, args.type),
  });

  return { create };
}
