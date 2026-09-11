"use client";

import { DicomUploader } from "@/components/medical/DicomUploader";
import { AppShell } from "@/components/ui/AppShell";
import { IconArrowRight, IconScan } from "@/components/ui/icons";

export default function UploadPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-3xl px-5 py-7">
        <div className="mb-6">
          <h2 className="text-xl font-semibold tracking-tight text-slate-900">Upload study</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Import a de-identified CT DICOM study into the workspace.
          </p>
        </div>

        <DicomUploader />

        <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
          {[
            { icon: IconScan, title: "1 · Validate", desc: "DICOM + CT series checks" },
            { icon: IconArrowRight, title: "2 · Order", desc: "Spatial slice ordering" },
            { icon: IconArrowRight, title: "3 · Reconstruct", desc: "3D volume + mesh" },
          ].map((s) => (
            <div key={s.title} className="surface surface-hover px-4 py-4">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <s.icon className="h-4 w-4" />
              </span>
              <p className="mt-2.5 text-sm font-semibold text-slate-800">{s.title}</p>
              <p className="mt-0.5 text-xs text-slate-500">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
