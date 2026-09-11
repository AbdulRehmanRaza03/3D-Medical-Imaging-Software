"use client";

import Link from "next/link";

import { useDashboard } from "@/hooks/useStudy";
import { StatusBadge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { IconActivity, IconCube, IconLayers, IconScan } from "@/components/ui/icons";

const metrics = [
  {
    key: "total_studies",
    label: "Total Studies",
    icon: IconLayers,
    color: "text-brand-600 bg-brand-50",
    default_: 0,
  },
  {
    key: "processed_studies",
    label: "Processed",
    icon: IconScan,
    color: "text-violet-600 bg-violet-50",
    default_: 0,
  },
  {
    key: "models_generated",
    label: "Models Generated",
    icon: IconCube,
    color: "text-emerald-600 bg-emerald-50",
    default_: 0,
  },
] as const;

export default function Dashboard() {
  const { data, isLoading } = useDashboard();

  const values = {
    total_studies: data?.total_studies ?? 0,
    processed_studies: data?.processed_studies ?? 0,
    models_generated: data?.models_generated ?? 0,
  };

  const recent = data?.recent_studies ?? [];
  const jobs = data?.processing_jobs ?? [];

  return (
    <div className="space-y-5">
      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {metrics.map((m) => (
          <Card key={m.key} className="surface-hover">
            <CardBody className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">{m.label}</p>
                <p className="mt-1.5 text-3xl font-semibold tracking-tight text-slate-900">
                  {isLoading ? (
                    <span className="inline-block h-7 w-10 animate-pulse rounded bg-slate-200" />
                  ) : (
                    values[m.key].toLocaleString()
                  )}
                </p>
              </div>
              <span className={`flex h-10 w-10 items-center justify-center rounded-lg ${m.color}`}>
                <m.icon className="h-5 w-5" />
              </span>
            </CardBody>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Recent studies */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Recent studies"
            subtitle={`${recent.length} study${recent.length === 1 ? "" : "ies"} shown`}
            action={
              <Link href="/upload" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                New study →
              </Link>
            }
          />
          {recent.length === 0 ? (
            <div className="flex flex-col items-center justify-center px-5 py-12 text-center">
              <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
                <IconScan className="h-6 w-6" />
              </span>
              <p className="mt-3 text-sm font-medium text-slate-600">No imaging studies yet</p>
              <p className="mt-1 max-w-xs text-xs text-slate-400">
                Upload a de-identified DICOM CT study to begin.
              </p>
              <Link href="/upload" className="btn-primary mt-4 px-4 py-2">
                Upload DICOM
              </Link>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {recent.map((s) => (
                <li key={s.id}>
                  <Link
                    href={`/study/${s.id}`}
                    className="flex items-center justify-between gap-3 px-5 py-3.5 transition hover:bg-slate-50"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-800">{s.name}</p>
                      <p className="mt-0.5 text-xs text-slate-400">
                        {s.modality ?? "—"} · {s.slice_count} slices ·{" "}
                        {new Date(s.created_at + "Z").toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </p>
                    </div>
                    <StatusBadge status={s.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Processing activity */}
        <Card>
          <CardHeader
            title="Processing"
            subtitle="Live reconstruction jobs"
            action={
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
                <IconActivity className="h-4 w-4" />
              </span>
            }
          />
          {jobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center px-5 py-12 text-center">
              <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
                <IconActivity className="h-6 w-6" />
              </span>
              <p className="mt-3 text-sm font-medium text-slate-600">No active jobs</p>
              <p className="mt-1 text-xs text-slate-400">Reconstruction jobs appear here.</p>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {jobs.map((j) => (
                <li key={j.id} className="px-5 py-3.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium capitalize text-slate-700">
                      {j.task_type.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs font-medium text-slate-500">
                      {Math.round(j.progress * 100)}%
                    </span>
                  </div>
                  <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-brand-500 transition-all"
                      style={{ width: `${Math.round(j.progress * 100)}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
