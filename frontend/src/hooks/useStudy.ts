"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api/client";

export function useStudy(id: number | null) {
  return useQuery({
    queryKey: ["study", id],
    queryFn: () => api.getStudy(id as number),
    enabled: id != null,
  });
}

export function useStudies() {
  return useQuery({
    queryKey: ["studies"],
    queryFn: () => api.listStudies(),
  });
}

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.getDashboard(),
  });
}

export function useMetadata(id: number | null) {
  return useQuery({
    queryKey: ["metadata", id],
    queryFn: () => api.getMetadata(id as number),
    enabled: id != null,
  });
}
