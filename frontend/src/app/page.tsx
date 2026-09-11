"use client";

import Dashboard from "@/components/Dashboard";
import { StudyList } from "@/components/medical/StudyList";
import { AppShell } from "@/components/ui/AppShell";
import { useStudies } from "@/hooks/useStudy";

export default function Home() {
  const { data, isLoading } = useStudies();

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl px-5 py-7 space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-xl font-semibold tracking-tight text-slate-900">Dashboard</h2>
            <p className="mt-0.5 text-sm text-slate-500">
              Overview of your imaging studies and reconstructions.
            </p>
          </div>
        </div>

        <Dashboard />

        <section>
          <h3 className="mb-3 text-sm font-semibold text-slate-700">All studies</h3>
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
