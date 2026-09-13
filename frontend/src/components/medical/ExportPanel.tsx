"use client";

import { api } from "@/lib/api/client";
import { IconDownload } from "@/components/ui/icons";

interface Props {
  modelId: number;
}

export function ExportPanel({ modelId }: Props) {
  const formats: ["stl" | "obj" | "glb", string][] = [
    ["stl", "STL"],
    ["obj", "OBJ"],
    ["glb", "GLB"],
  ];

  return (
    <div className="space-y-3">
      <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        Export
      </h4>
      <div className="flex flex-wrap gap-2">
        {formats.map(([fmt, label]) => (
          <a
            key={fmt}
            href={api.exportUrl(modelId, fmt)}
            download
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-800"
          >
            <IconDownload className="h-3.5 w-3.5" />
            {label}
          </a>
        ))}
      </div>
    </div>
  );
}
