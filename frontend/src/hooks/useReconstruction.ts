"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { api } from "@/lib/api/client";
import type { ReconstructRequest } from "@/types/medical";

/** Reconstruction submission + job-polling hook. */
export function useReconstruction(studyId: number | null) {
  const queryClient = useQueryClient();

  const models = useQuery({
    queryKey: ["models", studyId],
    queryFn: () => api.listModels(studyId as number),
    enabled: studyId != null,
  });

  const reconstruct = useMutation({
    mutationFn: (req: ReconstructRequest) =>
      api.reconstruct(studyId as number, req),
  });

  const jobId = reconstruct.data?.job_id ?? null;

  // Poll job status while a job is active.
  const job = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.getJob(jobId as string),
    enabled: jobId != null,
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Stop polling once the job reaches a terminal state.
      if (status === "completed" || status === "failed") return false;
      return 1000;
    },
    // A job that never resolves (e.g. worker died) must not poll forever.
    staleTime: Infinity,
  });

  // When job completes, refresh models.
  useEffect(() => {
    if (job.data?.status === "completed" || job.data?.status === "failed") {
      queryClient.invalidateQueries({ queryKey: ["models", studyId] });
      queryClient.invalidateQueries({ queryKey: ["study", studyId] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    }
  }, [job.data?.status, queryClient, studyId]);

  return { models, reconstruct, job };
}
