"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { IconLogo } from "./icons";

const links = [
  { href: "/", label: "Dashboard", exact: true },
  { href: "/upload", label: "Upload", exact: true },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen flex-col bg-slate-100">
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-5">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white shadow-sm">
              <IconLogo className="h-5 w-5" />
            </span>
            <span className="leading-tight">
              <span className="block text-[15px] font-semibold tracking-tight text-slate-900">
                OrthoVision AI
              </span>
              <span className="block text-[11px] font-medium text-slate-400">
                Medical 3D Imaging
              </span>
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            {links.map((l) => {
              const active = l.exact ? pathname === l.href : pathname.startsWith(l.href);
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                    active
                      ? "bg-slate-100 text-slate-900"
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                  }`}
                >
                  {l.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <span className="hidden rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-500 sm:inline-flex">
              v0.1 · Phase 1
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-5 py-4 text-xs leading-relaxed text-slate-400">
          <span className="font-semibold text-slate-500">OrthoVision AI</span> is a
          medical imaging research and visualization platform. It is not a
          diagnostic device and should not be used for clinical diagnosis or
          treatment decisions without appropriate validation, regulatory
          clearance, and clinical oversight.
        </div>
      </footer>
    </div>
  );
}
