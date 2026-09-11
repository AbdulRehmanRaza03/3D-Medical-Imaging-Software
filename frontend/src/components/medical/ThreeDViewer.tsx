"use client";

import { Canvas } from "@react-three/fiber";
import {
  GizmoHelper,
  GizmoViewport,
  Grid,
  OrbitControls,
  useGLTF,
} from "@react-three/drei";
import { Suspense, useMemo, useRef, useState } from "react";
import type { Group, Mesh } from "three";
import * as THREE from "three";

import { api } from "@/lib/api/client";
import type { Model } from "@/types/medical";
import { IconRefresh } from "@/components/ui/icons";

function ModelMesh({ url, wireframe }: { url: string; wireframe: boolean }) {
  const { scene } = useGLTF(url);
  const cloned = useMemo(() => scene.clone(), [scene]);

  return (
    <primitive
      object={cloned}
      onUpdate={(self: Group) => {
        self.traverse((child) => {
          if ((child as Mesh).isMesh) {
            (child as Mesh).material = new THREE.MeshStandardMaterial({
              color: 0xd7b58a,
              roughness: 0.6,
              metalness: 0.1,
              wireframe,
              side: THREE.DoubleSide,
            });
          }
        });
      }}
    />
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
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
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
}

export function ThreeDViewer({ model, markers, onAddMarker }: Props) {
  const [wireframe, setWireframe] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [showAxes, setShowAxes] = useState(true);
  const controlsRef = useRef<any>(null);

  const meshUrl = api.meshUrl(model.id);

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 px-3 py-2">
        <span className="text-xs text-slate-400">
          <span className="font-semibold text-slate-200">
            {model.vertices.toLocaleString()}
          </span>{" "}
          verts ·{" "}
          <span className="font-semibold text-slate-200">
            {model.triangles.toLocaleString()}
          </span>{" "}
          tris
        </span>
        <div className="flex flex-wrap items-center gap-1.5">
          <Toggle active={wireframe} onClick={() => setWireframe((w) => !w)}>
            Wireframe
          </Toggle>
          <Toggle active={showGrid} onClick={() => setShowGrid((g) => !g)}>
            Grid
          </Toggle>
          <Toggle active={showAxes} onClick={() => setShowAxes((a) => !a)}>
            Axes
          </Toggle>
          <button
            onClick={() => controlsRef.current?.reset?.()}
            className="flex items-center gap-1 rounded-md border border-slate-700 px-2.5 py-1 text-xs font-medium text-slate-300 transition hover:bg-slate-800"
          >
            <IconRefresh className="h-3.5 w-3.5" />
            Reset
          </button>
        </div>
      </div>

      <div className="flex-1">
        <Canvas camera={{ position: [120, 120, 120], fov: 45, near: 0.1, far: 5000 }}>
          <color attach="background" args={["#0f1726"]} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[200, 200, 200]} intensity={0.8} />
          <directionalLight position={[-200, -100, -200]} intensity={0.3} />

          <Suspense fallback={null}>
            <ModelMesh url={meshUrl} wireframe={wireframe} />
            <MeasurementMarkers markers={markers} />
          </Suspense>

          {showGrid && <Grid infiniteGrid sectionColor="#263445" cellColor="#18222f" />}
          {showAxes && (
            <GizmoHelper alignment="bottom-right" margin={[60, 60]}>
              <GizmoViewport axisColors={["#ef4444", "#22c55e", "#3b82f6"]} labelColor="white" />
            </GizmoHelper>
          )}

          <OrbitControls ref={controlsRef} makeDefault />
        </Canvas>
      </div>
    </div>
  );
}
