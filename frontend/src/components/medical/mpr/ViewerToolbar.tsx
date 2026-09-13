"use client";

import { useViewerStore, type InteractionMode } from "@/lib/viewer-store";

interface Tool {
  id: InteractionMode;
  label: string;
  shortcut: string;
  icon: string;
}

const tools: Tool[] = [
  { id: "select", label: "Select / Crosshair", shortcut: "1", icon: "⌖" },
  { id: "pan", label: "Pan", shortcut: "2", icon: "✋" },
  { id: "zoom", label: "Zoom", shortcut: "3", icon: "🔍" },
  { id: "window_level", label: "Window / Level", shortcut: "W", icon: "☼" },
  { id: "measure", label: "Measurement", shortcut: "M", icon: "📏" },
];

/**
 * Vertical tool rail for the medical viewer workspace. Each tool has an icon,
 * tooltip, active state, and keyboard shortcut.
 */
export function ViewerToolbar() {
  const interactionMode = useViewerStore((s) => s.interactionMode);
  const setInteractionMode = useViewerStore((s) => s.setInteractionMode);

  return (
    <div className="flex w-12 flex-col items-center gap-1 border-r border-slate-800 bg-slate-925 py-2">
      {tools.map((t) => {
        const active = interactionMode === t.id;
        return (
          <button
            key={t.id}
            title={`${t.label} (${t.shortcut})`}
            onClick={() => setInteractionMode(t.id)}
            className={`flex h-9 w-9 items-center justify-center rounded-md text-base transition ${
              active
                ? "border border-brand-500/60 bg-brand-500/15 text-brand-400"
                : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            <span aria-hidden>{t.icon}</span>
          </button>
        );
      })}

      <div className="my-2 h-px w-7 bg-slate-800" />

      <button
        title="Fit view (F)"
        onClick={() => useViewerStore.getState().resetView()}
        className="flex h-9 w-9 items-center justify-center rounded-md text-base text-slate-400 transition hover:bg-slate-800 hover:text-slate-200"
      >
        ⛶
      </button>
      <button
        title="Reset (R)"
        onClick={() => useViewerStore.getState().resetView()}
        className="flex h-9 w-9 items-center justify-center rounded-md text-base text-slate-400 transition hover:bg-slate-800 hover:text-slate-200"
      >
        ↻
      </button>
    </div>
  );
}
