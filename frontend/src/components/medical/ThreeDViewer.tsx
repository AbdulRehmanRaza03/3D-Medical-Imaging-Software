"use client";

import { Canvas } from "@react-three/fiber";
import {
  GizmoHelper,
  GizmoViewport,
  Grid,
  OrbitControls,
  useGLTF,
} from "@react-three/drei";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import type { Group, Mesh } from "three";
import * as THREE from "three";

import { api } from "@/lib/api/client";
import { useViewerStore } from "@/lib/viewer-store";
import type { Model } from "@/types/medical";
import { IconRefresh } from "@/components/ui/icons";

function ModelMesh({
  url,
  wireframe,
  opacity,
  clipping,
}: {
  url: string;
  wireframe: boolean;
  opacity: number;
  clipping: { x: number | null; y: number | null; z: number | null };
}) {
  const { scene } = useGLTF(url);
  const cloned = useMemo(() => scene.clone(), [scene]);

  const clipPlanes = useMemo(() => {
    const planes: THREE.Plane[] = [];
    if (clipping.x != null) planes.push(new THREE.Plane(new THREE.Vector3(-1, 0, 0), clipping.x));
    if (clipping.y != null) planes.push(new THREE.Plane(new THREE.Vector3(0, -1, 0), clipping.y));
    if (clipping.z != null) planes.push(new THREE.Plane(new THREE.Vector3(0, 0, -1), clipping.z));
    return planes;
  }, [clipping]);

  // Apply material properties (opacity, wireframe, clipping) on scene.
  useEffect(() => {
    cloned.traverse((child: THREE.Object3D) => {
      if ((child as Mesh).isMesh) {
        const mat = (child as Mesh).material as THREE.MeshStandardMaterial;
        mat.wireframe = wireframe;
        mat.opacity = opacity;
        mat.transparent = opacity < 1.0;
        mat.clippingPlanes = clipPlanes;
        mat.needsUpdate = true;
      }
    });
  }, [cloned, wireframe, opacity, clipPlanes]);

  return <primitive object={cloned} />;
}

function MprPlane({
  size,
  position,
  rotation,
  color,
  visible,
}: {
  size: [number, number];
  position: [number, number, number];
  rotation: [number, number, number];
  color: string;
  visible: boolean;
}) {
  if (!visible) return null;
  return (
    <mesh position={position} rotation={rotation}>
      <planeGeometry args={size} />
      <meshBasicMaterial color={color} transparent opacity={0.15} side={THREE.DoubleSide} />
    </mesh>
  );
}

function MeasurementMarkers({ markers }: { markers: [number, number, number][] }) {
  return (
    <>
      {markers.map((m, i) => (
        <mesh key={i} position={m}>
          <sphereGeometry args={[1.5, 16, 16]} />
          <meshBasicMaterial color={0xff5533} />
        </mesh>
      ))}
    </>
  );
}

function Toggle({
  active,
  onClick,
  children,
  title,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  title?: string;
}) {
  return (
    <button
      title={title}
      onClick={onClick}
      className={`rounded-md border px-2.5 py-1 text-xs font-medium transition ${
        active
          ? "border-brand-500/60 bg-brand-500/15 text-brand-300"
          : "border-slate-700 text-slate-300 hover:bg-slate-800"
      }`}
    >
      {children}
    </button>
  );
}

interface Props {
  model: Model;
  markers: [number, number, number][];
  onAddMarker: (point: [number, number, number]) => void;
  volumeShape?: [number, number, number]; // depth, height, width
  spacing?: [number, number, number];
}

export function ThreeDViewer({ model, markers, onAddMarker, volumeShape, spacing }: Props) {
  const wireframe = useViewerStore((s) => s.wireframe);
  const toggleWireframe = useViewerStore((s) => s.toggleWireframe);
  const showGrid = useViewerStore((s) => s.showGrid);
  const toggleGrid = useViewerStore((s) => s.toggleGrid);
  const showAxes = useViewerStore((s) => s.showAxes);
  const toggleAxes = useViewerStore((s) => s.toggleAxes);
  const opacity = useViewerStore((s) => s.modelOpacity);
  const setOpacity = useViewerStore((s) => s.setModelOpacity);
  const cameraMode = useViewerStore((s) => s.cameraMode);
  const setCameraMode = useViewerStore((s) => s.setCameraMode);
  const clipping = useViewerStore((s) => s.clipping);
  const setClipping = useViewerStore((s) => s.setClipping);
  const showAxialPlane = useViewerStore((s) => s.showAxialPlane);
  const showCoronalPlane = useViewerStore((s) => s.showCoronalPlane);
  const showSagittalPlane = useViewerStore((s) => s.showSagittalPlane);
  const togglePlane = useViewerStore((s) => s.togglePlane);
  const crosshair = useViewerStore((s) => s.crosshair);

  const controlsRef = useRef<any>(null);
  const meshUrl = api.meshUrl(model.id);

  // Compute plane size from physical dimensions of the volume.
  const [planeSize, setPlaneSize] = useState<[number, number]>([100, 100]);
  useEffect(() => {
    if (volumeShape && spacing) {
      const [depth, height, width] = volumeShape;
      const [sx, sy, sz] = spacing;
      // axial plane spans x and y.
      setPlaneSize([width * sx, height * sy]);
    }
  }, [volumeShape, spacing]);

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 px-3 py-1.5">
        <span className="text-xs text-slate-400">
          <span className="font-semibold text-slate-200">{model.vertices.toLocaleString()}</span>{" "}
          verts
        </span>
        <div className="flex flex-wrap items-center gap-1.5">
          <Toggle active={showGrid} onClick={toggleGrid} title="Toggle grid">Grid</Toggle>
          <Toggle active={showAxes} onClick={toggleAxes} title="Toggle axes">Axes</Toggle>
          <Toggle active={wireframe} onClick={toggleWireframe} title="Toggle wireframe">Wire</Toggle>
          <Toggle active={cameraMode === "orthographic"} onClick={() => setCameraMode(cameraMode === "orthographic" ? "perspective" : "orthographic")} title="Toggle camera">Ortho</Toggle>
          <button
            onClick={() => controlsRef.current?.reset?.()}
            className="flex items-center gap-1 rounded-md border border-slate-700 px-2.5 py-1 text-xs font-medium text-slate-300 transition hover:bg-slate-800"
          >
            <IconRefresh className="h-3.5 w-3.5" />
            Reset
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1">
        <Canvas
          orthographic={cameraMode === "orthographic"}
          camera={{ position: [120, 120, 120], fov: 45, near: 0.1, far: 5000 }}
        >
          <color attach="background" args={["#0b0f14"]} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[200, 200, 200]} intensity={0.9} />
          <directionalLight position={[-200, -100, -200]} intensity={0.35} />

          <Suspense fallback={null}>
            <ModelMesh
              url={meshUrl}
              wireframe={wireframe}
              opacity={opacity}
              clipping={clipping}
            />
            <MeasurementMarkers markers={markers} />

            {/* MPR reference planes */}
            <MprPlane
              size={planeSize}
              position={[planeSize[0] / 2, planeSize[1] / 2, crosshair.z]}
              rotation={[0, 0, 0]}
              color="#38bdf8"
              visible={showAxialPlane}
            />
          </Suspense>

          {showGrid && <Grid infiniteGrid sectionColor="#1a2632" cellColor="#0f1720" />}
          {showAxes && (
            <GizmoHelper alignment="bottom-right" margin={[60, 60]}>
              <GizmoViewport axisColors={["#ef4444", "#22c55e", "#3b82f6"]} labelColor="white" />
            </GizmoHelper>
          )}

          <OrbitControls ref={controlsRef} makeDefault />
        </Canvas>
      </div>

      {/* Opacity + clipping controls */}
      <div className="border-t border-slate-800 px-3 py-1.5 space-y-1.5">
        {/* Opacity */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-500">Opacity</span>
          <input
            type="range"
            min={0.05}
            max={1}
            step={0.01}
            value={opacity}
            onChange={(e) => setOpacity(Number(e.target.value))}
            className="h-1 flex-1 cursor-pointer appearance-none rounded-full bg-slate-700 accent-brand-500"
            aria-label="Model opacity"
          />
          <span className="w-9 text-right font-mono text-[11px] text-slate-300">
            {Math.round(opacity * 100)}%
          </span>
        </div>

        {/* Reference planes toggles */}
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-slate-500">Planes</span>
          <Toggle active={showAxialPlane} onClick={() => togglePlane("axial")}>A</Toggle>
          <Toggle active={showCoronalPlane} onClick={() => togglePlane("coronal")}>C</Toggle>
          <Toggle active={showSagittalPlane} onClick={() => togglePlane("sagittal")}>S</Toggle>
        </div>
      </div>
    </div>
  );
}
