"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { SliceResponse } from "@/types/medical";
import { IconRefresh } from "@/components/ui/icons";

interface Props {
  slice: SliceResponse | undefined;
  index: number;
  total: number;
  onIndexChange: (index: number) => void;
}

export function SliceViewer({ slice, index, total, onIndexChange }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!slice?.image_base64) return;
    const img = new Image();
    img.onload = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
    };
    img.src = `data:image/png;base64,${slice.image_base64}`;
  }, [slice]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.style.transform = `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`;
    canvas.style.transformOrigin = "center center";
  }, [zoom, pan]);

  const onWheel = useCallback(
    (e: React.WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.1 : 0.9;
        setZoom((z) => Math.min(8, Math.max(0.1, z * factor)));
      } else {
        const dir = e.deltaY > 0 ? 1 : -1;
        onIndexChange(Math.max(0, Math.min(total - 1, index + dir)));
      }
    },
    [index, total, onIndexChange],
  );

  const onMouseDown = (e: React.MouseEvent) => {
    dragging.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
  };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!dragging.current) return;
    const dx = e.clientX - lastPos.current.x;
    const dy = e.clientY - lastPos.current.y;
    lastPos.current = { x: e.clientX, y: e.clientY };
    setPan((p) => ({ x: p.x + dx / zoom, y: p.y + dy / zoom }));
  };
  const onMouseUp = () => {
    dragging.current = false;
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Axial
          </span>
          <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-200">
            {index + 1} / {total}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-slate-500">{Math.round(zoom * 100)}%</span>
          <button
            onClick={resetView}
            className="flex items-center gap-1 rounded border border-slate-700 px-2 py-1 text-xs text-slate-300 transition hover:bg-slate-800"
          >
            <IconRefresh className="h-3.5 w-3.5" />
            Reset
          </button>
        </div>
      </div>

      {/* Canvas area */}
      <div
        className="relative flex-1 overflow-hidden bg-slate-950"
        onWheel={onWheel}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        style={{ cursor: dragging.current ? "grabbing" : "grab" }}
      >
        <div className="flex h-full items-center justify-center overflow-hidden p-4">
          <canvas ref={canvasRef} className="max-w-full max-h-full" />
        </div>

        {/* Corner orientation hint */}
        <span className="pointer-events-none absolute left-3 top-3 font-mono text-[10px] uppercase tracking-wider text-slate-600">
          A
        </span>
        <span className="pointer-events-none absolute left-3 bottom-3 font-mono text-[10px] uppercase tracking-wider text-slate-600">
          L
        </span>
      </div>

      {/* Slider */}
      <div className="border-t border-slate-800 px-3 py-2.5">
        <input
          type="range"
          min={0}
          max={Math.max(0, total - 1)}
          value={index}
          onChange={(e) => onIndexChange(Number(e.target.value))}
          className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-slate-700 accent-brand-500"
          aria-label="Slice slider"
        />
      </div>
    </div>
  );
}
