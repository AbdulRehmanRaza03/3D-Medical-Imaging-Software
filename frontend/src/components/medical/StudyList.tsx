"use client";

import Link from "next/link";

import type { Study } from "@/types/medical";
import { StatusBadge } from "@/components/ui/Badge";
import { IconArrowRight, IconScan } from "@/components/ui/icons";

export function StudyList({ studies }: { studies: Study[] }) {
  if (studies.length === 0) {
    return (
      <div className="surface flex flex-col items-center justify-center px-6 py-14 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
          <IconScan className="h-7 w-7" />
        </span>
        <p className="mt-4 text-sm font-medium text-slate-600">No imaging studies yet</p>
        <p className="mt-1 max-w-sm text-xs text-slate-400">
          Upload a de-identified DICOM CT study to begin.
        </p>
      </div>
    );
  }

  return (
    <div className="surface overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-100 text-sm">
          <thead>
            <tr className="bg-slate-50/70 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
              <th className="px-5 py-3">Study name</th>
              <th className="px-5 py-3">Modality</th>
              <th className="px-5 py-3">Slices</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3">Uploaded</th>
              <th className="px-5 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {studies.map((s) => (
              <tr key={s.id} className="group transition hover:bg-slate-50/70">
                <td className="px-5 py-3.5">
                  <p className="font-medium text-slate-800">{s.name}</p>
                  <p className="mt-0.5 font-mono text-xs text-slate-400">
                    {s.study_uid.slice(0, 12)}…
                  </p>
                </td>
                <td className="px-5 py-3.5 text-slate-600">{s.modality ?? "—"}</td>
                <td className="px-5 py-3.5 text-slate-600">{s.slice_count}</td>
                <td className="px-5 py-3.5">
                  <StatusBadge status={s.status} />
                </td>
                <td className="px-5 py-3.5 text-slate-500">
                  {new Date(s.created_at + "Z").toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </td>
                <td className="px-5 py-3.5 text-right">
                  <Link
                    href={`/study/${s.id}`}
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 transition group-hover:gap-2.5 hover:text-brand-700"
                  >
                    Open viewer
                    <IconArrowRight className="h-4 w-4" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
