"use client";

import Link from "next/link";

import { useDashboard } from "@/hooks/useStudy";
import { StatusBadge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import {
  IconActivity,
  IconArrowRight,
  IconArrowUp,
  IconChart,
  IconCheckCircle,
  IconCube,
  IconFile,
  IconLayers,
  IconScan,
  IconTrend,
} from "@/components/ui/icons";

/* ------------------------------------------------------------------ */
/*  Small building blocks                                             */
/* ------------------------------------------------------------------ */

function StatDelta({ value }: { value: string }) {
  return (
    <span className="inline-flex items-center gap-0.5 text-xs font-medium text-emerald-600">
      <IconArrowUp className="h-3 w-3" />
      {value}
    </span>
  );
}

function ProgressBar({
  value,
  tone = "bg-brand-500",
}: {
  value: number; // 0..1
  tone?: string;
}) {
  const pct = Math.round(Math.min(1, Math.max(0, value)) * 100);
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
      <div
        className={`h-full rounded-full transition-all duration-500 ${tone}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function RelativeTime({ iso }: { iso: string }) {
  try {
    const d = new Date(iso + (iso.endsWith("Z") ? "" : "Z"));
    const diff = Date.now() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return <span>just now</span>;
    if (mins < 60) return <span>{mins}m ago</span>;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return <span>{hrs}h ago</span>;
    const days = Math.floor(hrs / 24);
    if (days < 7) return <span>{days}d ago</span>;
    return (
      <span>
        {d.toLocaleDateString(undefined, {
          month: "short",
          day: "numeric",
          year: "numeric",
        })}
      </span>
    );
  } catch {
    return <span>—</span>;
  }
}

/* ------------------------------------------------------------------ */
/*  Components                                                        */
/* ------------------------------------------------------------------ */

function StatCard({
  label,
  value,
  icon: Icon,
  accent,
  delta,
  hint,
}: {
  label: string;
  value: string;
  icon: (p: any) => JSX.Element;
  accent: string;
  delta?: string;
  hint?: string;
}) {
  return (
    <Card className="relative overflow-hidden">
      <CardBody className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-[28px] font-semibold leading-none tracking-tight text-slate-900 tabular-nums">
            {value}
          </p>
          <div className="mt-2.5 flex items-center gap-2">
            {delta && <StatDelta value={delta} />}
            {hint && <span className="text-[11px] text-slate-400">{hint}</span>}
          </div>
        </div>
        <span
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${accent}`}
        >
          <Icon className="h-[22px] w-[22px]" />
        </span>
      </CardBody>
    </Card>
  );
}

function StatusDonut({ data }: { data: { uploaded: number; processing: number; ready: number; failed: number } }) {
  const total = data.uploaded + data.processing + data.ready + data.failed || 1;
  const segments = [
    { label: "Ready", value: data.ready, color: "#10b981" },
    { label: "Processing", value: data.processing, color: "#f59e0b" },
    { label: "Uploaded", value: data.uploaded, color: "#6366f1" },
    { label: "Failed", value: data.failed, color: "#ef4444" },
  ];
  const R = 40;
  const C = 2 * Math.PI * R;
  let offset = 0;

  return (
    <div className="flex items-center gap-6">
      <div className="relative h-28 w-28 shrink-0">
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
          <circle cx="50" cy="50" r={R} fill="none" stroke="#f1f5f9" strokeWidth="12" />
          {segments.map((s) => {
            const frac = s.value / total;
            const dash = frac * C;
            const el = (
              <circle
                key={s.label}
                cx="50"
                cy="50"
                r={R}
                fill="none"
                stroke={s.color}
                strokeWidth="12"
                strokeDasharray={`${dash} ${C - dash}`}
                strokeDashoffset={-offset}
                strokeLinecap="butt"
              />
            );
            offset += dash;
            return el;
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-semibold tabular-nums text-slate-900">{total}</span>
          <span className="text-[10px] uppercase tracking-wide text-slate-400">studies</span>
        </div>
      </div>
      <ul className="space-y-2">
        {segments.map((s) => (
          <li key={s.label} className="flex items-center gap-2 text-xs">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
            <span className="text-slate-500">{s.label}</span>
            <span className="ml-auto font-medium tabular-nums text-slate-700">{s.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Dashboard() {
  const { data, isLoading } = useDashboard();

  const studies = data?.recent_studies ?? [];
  const queue = data?.processing_jobs ?? [];
  const recentJobs = data?.recent_jobs ?? [];

  const total = data?.total_studies ?? 0;
  const processed = data?.processed_studies ?? 0;
  const models = data?.models_generated ?? 0;
  const failed = data?.failed_studies ?? 0;
  const uploaded = data?.uploaded_studies ?? 0;
  const processing = total - processed - failed - uploaded;
  const series = data?.total_series ?? 0;
  const slices = data?.total_slices ?? 0;

  const successRate = total > 0 ? Math.round((processed / total) * 100) : 0;

  const statCards = [
    {
      label: "Total Studies",
      value: total.toLocaleString(),
      icon: IconLayers,
      accent: "bg-brand-50 text-brand-600",
      hint: `${series} series`,
    },
    {
      label: "3D Models",
      value: models.toLocaleString(),
      icon: IconCube,
      accent: "bg-violet-50 text-violet-600",
      delta: uploaded > 0 ? `+${uploaded}` : undefined,
      hint: "reconstructed",
    },
    {
      label: "Success Rate",
      value: `${successRate}%`,
      icon: IconChart,
      accent: "bg-emerald-50 text-emerald-600",
      hint: `${processed} processed`,
    },
    {
      label: "Total Slices",
      value: slices.toLocaleString(),
      icon: IconFile,
      accent: "bg-sky-50 text-sky-600",
      hint: "processed voxels",
    },
  ];

  return (
    <div className="space-y-5">
      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map((c) => (
          <StatCard key={c.label} {...c} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Recent studies */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Recent studies"
            subtitle={`${studies.length} most recent`}
            action={
              <Link
                href="/upload"
                className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                New study <IconArrowRight className="h-4 w-4" />
              </Link>
            }
          />
          {studies.length === 0 ? (
            <div className="flex flex-col items-center justify-center px-5 py-14 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
                <IconScan className="h-7 w-7" />
              </span>
              <p className="mt-4 text-sm font-medium text-slate-600">No imaging studies yet</p>
              <p className="mt-1 max-w-xs text-xs text-slate-400">
                Upload a de-identified DICOM CT study to begin.
              </p>
              <Link href="/upload" className="btn-primary mt-4 px-4 py-2">
                Upload DICOM
              </Link>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {studies.map((s) => (
                <li key={s.id}>
                  <Link
                    href={`/study/${s.id}`}
                    className="group flex items-center justify-between gap-3 px-5 py-3.5 transition hover:bg-slate-50"
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-400 group-hover:bg-brand-50 group-hover:text-brand-600">
                        <IconScan className="h-4 w-4" />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-slate-800">{s.name}</p>
                        <p className="mt-0.5 text-xs text-slate-400">
                          {s.modality ?? "—"} · {s.slice_count} slices ·{" "}
                          <RelativeTime iso={s.created_at} />
                        </p>
                      </div>
                    </div>
                    <StatusBadge status={s.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Right column */}
        <div className="space-y-4">
          {/* Status distribution */}
          <Card>
            <CardHeader
              title="Status"
              subtitle="Study distribution"
              action={
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                  <IconChart className="h-4 w-4" />
                </span>
              }
            />
            <CardBody>
              {total === 0 ? (
                <p className="py-8 text-center text-xs text-slate-400">
                  No data yet.
                </p>
              ) : (
                <StatusDonut
                  data={{ uploaded, processing, ready: processed, failed }}
                />
              )}
            </CardBody>
          </Card>

          {/* Throughput summary */}
          <Card>
            <CardHeader title="Pipeline" subtitle="Throughput summary" />
            <CardBody className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Series detected</span>
                <span className="font-medium tabular-nums text-slate-800">{series}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Models generated</span>
                <span className="font-medium tabular-nums text-slate-800">{models}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Failed studies</span>
                <span
                  className={`font-medium tabular-nums ${failed > 0 ? "text-red-600" : "text-slate-800"}`}
                >
                  {failed}
                </span>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>

      {/* Processing queue */}
      <Card>
        <CardHeader
          title="Processing queue"
          subtitle={queue.length > 0 ? `${queue.length} active job${queue.length > 1 ? "s" : ""}` : "Idle"}
          action={
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
              <IconActivity className="h-4 w-4" />
            </span>
          }
        />
        {queue.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-5 py-12 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
              <IconCheckCircle className="h-6 w-6" />
            </span>
            <p className="mt-3 text-sm font-medium text-slate-600">No active jobs</p>
            <p className="mt-1 text-xs text-slate-400">
              Reconstruction jobs appear here in real time.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {queue.map((j) => (
              <li key={j.id} className="px-5 py-3.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />
                    <span className="text-sm font-medium capitalize text-slate-700">
                      {j.task_type.replace(/_/g, " ")}
                    </span>
                  </div>
                  <span className="text-xs font-medium tabular-nums text-slate-500">
                    {j.message ?? ""} · {Math.round(j.progress * 100)}%
                  </span>
                </div>
                <div className="mt-2">
                  <ProgressBar value={j.progress} tone="bg-amber-500" />
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* Recent activity (jobs) */}
      {recentJobs.length > 0 && (
        <Card>
          <CardHeader
            title="Recent activity"
            subtitle="Latest processing events"
            action={
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                <IconTrend className="h-4 w-4" />
              </span>
            }
          />
          <ul className="divide-y divide-slate-100">
            {recentJobs.map((j) => (
              <li key={j.id} className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  <span
                    className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                      j.status === "completed"
                        ? "bg-emerald-50 text-emerald-600"
                        : j.status === "failed"
                        ? "bg-red-50 text-red-600"
                        : "bg-slate-100 text-slate-400"
                    }`}
                  >
                    {j.status === "completed" ? (
                      <IconCheckCircle className="h-4 w-4" />
                    ) : (
                      <IconActivity className="h-4 w-4" />
                    )}
                  </span>
                  <div>
                    <p className="text-sm font-medium capitalize text-slate-700">
                      {j.task_type.replace(/_/g, " ")}
                    </p>
                    <p className="text-xs text-slate-400">
                      Study #{j.study_id} · <RelativeTime iso={j.created_at} />
                    </p>
                  </div>
                </div>
                <StatusBadge status={j.status} />
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
