"use client";

import type { ReactNode } from "react";

type Tone = "neutral" | "blue" | "green" | "amber" | "red" | "violet";

const tones: Record<Tone, string> = {
  neutral: "bg-slate-100 text-slate-600 ring-slate-200",
  blue: "bg-brand-50 text-brand-700 ring-brand-200",
  green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  amber: "bg-amber-50 text-amber-700 ring-amber-200",
  red: "bg-red-50 text-red-700 ring-red-200",
  violet: "bg-violet-50 text-violet-700 ring-violet-200",
};

export function Badge({
  children,
  tone = "neutral",
  className = "",
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { tone: Tone; label: string }> = {
    uploaded: { tone: "neutral", label: "Uploaded" },
    processing: { tone: "amber", label: "Processing" },
    ready: { tone: "green", label: "Ready" },
    failed: { tone: "red", label: "Failed" },
    queued: { tone: "neutral", label: "Queued" },
    completed: { tone: "green", label: "Completed" },
  };
  const { tone, label } = map[status] ?? { tone: "neutral", label: status };
  return <Badge tone={tone}>{label}</Badge>;
}
