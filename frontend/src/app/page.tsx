"use client";

import Link from "next/link";

import Dashboard from "@/components/Dashboard";
import { StudyList } from "@/components/medical/StudyList";
import { AppShell } from "@/components/ui/AppShell";
import { IconArrowRight, IconUpload } from "@/components/ui/icons";
import { useStudies } from "@/hooks/useStudy";

export default function Home() {
  const { data, isLoading } = useStudies();
  const hasStudies = (data?.studies ?? []).length > 0;

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl px-5 py-7 space-y-6">
        {/* Hero */}
        <section className="surface overflow-hidden">
          <div className="flex flex-col gap-5 px-6 py-7 sm:flex-row sm:items-center sm:justify-between">
            <div className="max-w-xl">
              <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                Medical 3D imaging workspace
              </h2>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-500">
                Transform de-identified CT DICOM studies into interactive,
                anatomically accurate 3D models — with MPR, measurements, and export.
              </p>
            </div>
            <Link href="/upload" className="btn-primary shrink-0 px-4 py-2.5">
              <IconUpload className="h-4 w-4" />
              Upload study
            </Link>
          </div>
        </section>

        <Dashboard />

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700">All studies</h3>
            {hasStudies && (
              <span className="text-xs font-medium text-slate-400">
                {data?.total} total
              </span>
            )}
          </div>
          {isLoading ? (
            <div className="space-y-2">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-14 animate-pulse rounded-lg bg-slate-200/60" />
              ))}
            </div>
          ) : (
            <StudyList studies={data?.studies ?? []} />
          )}
        </section>
      </div>
    </AppShell>
  );
}
