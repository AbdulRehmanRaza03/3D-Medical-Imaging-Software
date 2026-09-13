"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { MprSlice, PlaneName } from "@/types/medical";
import type { InteractionMode } from "@/lib/viewer-store";
import { OrientationMarkers } from "./OrientationMarkers";

interface Props {
  plane: PlaneName;
  slice: MprSlice | undefined;
  index: number;
  total: number;
  onIndexChange: (index: number) => void;
  active: boolean;
  onActivate: () => void;
  interactionMode: InteractionMode;
  onWindowLevel: (width: number, level: number) => void;
  windowWidth: number;
  windowLevel: number;
  /** Optional crosshair overlay position in normalized [0,1] image coords. */
  crosshair?: { x: number; y: number } | null;
}

/**
 * A single MPR panel: renders a windowed 2D slice to a canvas with zoom/pan,
 * wheel-based slice navigation, window/level interaction, and a crosshair.
 */
export function PlaneViewer({
  plane,
  slice,
  index,
  total,
  onIndexChange,
  active,
  onActivate,
  interactionMode,
  onWindowLevel,
  windowWidth,
  windowLevel,
  crosshair,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  // Draw the slice image.
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

      // Draw crosshair overlay if present.
      if (crosshair) {
        const cx = crosshair.x * canvas.width;
        const cy = crosshair.y * canvas.height;
        ctx.strokeStyle = "rgba(56, 189, 248, 0.85)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(cx, 0);
        ctx.lineTo(cx, canvas.height);
        ctx.moveTo(0, cy);
        ctx.lineTo(canvas.width, cy);
        ctx.stroke();
        // Center dot.
        ctx.fillStyle = "rgba(56, 189, 248, 0.9)";
        ctx.beginPath();
        ctx.arc(cx, cy, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    };
    img.src = `data:image/png;base64,${slice.image_base64}`;
  }, [slice, crosshair]);

  // Apply zoom/pan transform.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.style.transform = `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`;
    canvas.style.transformOrigin = "center center";
  }, [zoom, pan]);

  const onWheel = useCallback(
    (e: React.WheelEvent) => {
      if (interactionMode === "zoom" || e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.1 : 0.9;
        setZoom((z) => Math.min(8, Math.max(0.1, z * factor)));
        return;
      }
      // Default: slice navigation.
      const dir = e.deltaY > 0 ? 1 : -1;
      onIndexChange(Math.max(0, Math.min(total - 1, index + dir)));
    },
    [index, total, onIndexChange, interactionMode],
  );

  const onMouseDown = (e: React.MouseEvent) => {
    onActivate();
    dragging.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (!dragging.current) return;
    if (interactionMode === "pan") {
      const dx = e.clientX - lastPos.current.x;
      const dy = e.clientY - lastPos.current.y;
      lastPos.current = { x: e.clientX, y: e.clientY };
      setPan((p) => ({ x: p.x + dx / zoom, y: p.y + dy / zoom }));
    } else if (interactionMode === "window_level") {
      // Horizontal → width, vertical → level.
      const dx = e.clientX - lastPos.current.x;
      const dy = e.clientY - lastPos.current.y;
      lastPos.current = { x: e.clientX, y: e.clientY };
      onWindowLevel(
        Math.max(1, windowWidth + dx * 4),
        windowLevel + dy * 2,
      );
    }
  };

  const onMouseUp = () => {
    dragging.current = false;
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const label = plane.toUpperCase();

  return (
    <div
      className={`flex h-full flex-col rounded-lg border transition-colors ${
        active ? "border-brand-500/70" : "border-slate-700/60"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 px-2.5 py-1.5">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </span>
        <span className="font-mono text-[11px] text-slate-400">
          Slice {index + 1} / {total}
        </span>
      </div>

      {/* Canvas area */}
      <div
        ref={containerRef}
        className="relative flex-1 overflow-hidden bg-slate-950"
        onWheel={onWheel}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onClick={onActivate}
        style={{ cursor: interactionMode === "pan" ? "grab" : "crosshair" }}
      >
        <div className="flex h-full items-center justify-center overflow-hidden p-2">
          <canvas ref={canvasRef} className="max-w-full max-h-full" />
        </div>

        <OrientationMarkers plane={plane} />

        {/* Zoom indicator */}
        <span className="pointer-events-none absolute bottom-1.5 right-2 font-mono text-[10px] text-slate-600">
          {Math.round(zoom * 100)}%
        </span>

        {/* Window/level active indicator */}
        {interactionMode === "window_level" && active && (
          <span className="pointer-events-none absolute left-2 bottom-1.5 rounded bg-brand-500/20 px-1.5 py-0.5 font-mono text-[10px] text-brand-300">
            W/L
          </span>
        )}
      </div>

      {/* Slider */}
      <div className="border-t border-slate-800 px-2.5 py-1.5">
        <input
          type="range"
          min={0}
          max={Math.max(0, total - 1)}
          value={index}
          onChange={(e) => onIndexChange(Number(e.target.value))}
          className="h-1 w-full cursor-pointer appearance-none rounded-full bg-slate-700 accent-brand-500"
          aria-label={`${plane} slice slider`}
        />
      </div>
    </div>
  );
}
