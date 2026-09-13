"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { api } from "@/lib/api/client";

/** AI segmentation panel hook: models, run job, poll status, list results. */
export function useSegmentation(studyId: number | null) {
  const queryClient = useQueryClient();

  const models = useQuery({
    queryKey: ["segmentation-models"],
    queryFn: () => api.listSegmentationModels(),
  });

  const results = useQuery({
    queryKey: ["segmentations", studyId],
    queryFn: () => api.listSegmentations(studyId as number),
    enabled: studyId != null,
  });

  const run = useMutation({
    mutationFn: (modelId: string) => api.createSegmentationJob(studyId as number, modelId),
  });

  const jobId = run.data?.job_id ?? null;

  const job = useQuery({
    queryKey: ["segmentation-job", jobId],
    queryFn: () => api.getSegmentationJob(jobId as string),
    enabled: jobId != null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 1000;
    },
  });

  useEffect(() => {
    if (job.data?.status === "completed" || job.data?.status === "failed") {
      queryClient.invalidateQueries({ queryKey: ["segmentations", studyId] });
    }
  }, [job.data?.status, queryClient, studyId]);

  return { models, results, run, job };
}
