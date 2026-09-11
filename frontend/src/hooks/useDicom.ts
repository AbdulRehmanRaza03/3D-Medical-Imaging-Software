"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api/client";

/** Upload + ingestion workflow hook. */
export function useDicom() {
  const queryClient = useQueryClient();

  const upload = useMutation({
    mutationFn: (args: { files: File[]; name?: string }) =>
      api.uploadStudy(args.files, args.name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["studies"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  return { upload };
}
