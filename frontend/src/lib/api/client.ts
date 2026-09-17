/** Typed API client for the OrthoVision AI backend. */

import type {
  CoordinateInfo,
  DashboardStats,
  Job,
  Measurement,
  Metadata,
  Model,
  MprSlice,
  PlaneName,
  ReconstructRequest,
  SegmentationJobResponse,
  SegmentationJobStatus,
  SegmentationModelInfo,
  SegmentationResult,
  SliceResponse,
  Study,
  StudyDetail,
  UploadResult,
  VolumeInfo,
} from "@/types/medical";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export class ApiError extends Error {
  status: number;
  code: string | null;

  constructor(message: string, status: number, code: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    // Normalize the path to always begin with a single leading slash.
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    res = await fetch(`${API_BASE}${normalizedPath}`, init);
  } catch (err) {
    throw new ApiError(
      "Network error — could not reach the backend server.",
      0,
      "network_error",
    );
  }

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    let code: string | null = null;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
      if (body?.code) code = body.code;
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(detail, res.status, code);
  }

  return (await res.json()) as T;
}

export const api = {
  async uploadStudy(files: File[], name?: string): Promise<UploadResult> {
    const form = new FormData();
    for (const f of files) form.append("files", f);
    if (name) form.append("name", name);
    return request<UploadResult>("/api/v1/studies/upload", {
      method: "POST",
      body: form,
    });
  },

  listStudies(): Promise<{ studies: Study[]; total: number }> {
    return request("/api/v1/studies");
  },

  getStudy(id: number): Promise<StudyDetail> {
    return request(`/api/v1/studies/${id}`);
  },

  getMetadata(id: number): Promise<Metadata> {
    return request(`/api/v1/studies/${id}/metadata`);
  },

  getSliceInfo(id: number): Promise<SliceResponse> {
    return request(`/api/v1/studies/${id}/slices`);
  },

  getSlice(
    id: number,
    index: number,
    width?: number,
    level?: number,
  ): Promise<SliceResponse> {
    const params = new URLSearchParams();
    if (width != null) params.set("width", String(width));
    if (level != null) params.set("level", String(level));
    const qs = params.toString();
    return request(`/api/v1/studies/${id}/slice/${index}${qs ? `?${qs}` : ""}`);
  },

  reconstruct(id: number, req: ReconstructRequest): Promise<{ job_id: string }> {
    return request(`/api/v1/studies/${id}/reconstruct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
  },

  listModels(id: number): Promise<{ models: Model[] }> {
    return request(`/api/v1/studies/${id}/models`);
  },

  getModel(id: number): Promise<Model> {
    return request(`/api/v1/models/${id}`);
  },

  getJob(jobId: string): Promise<Job> {
    return request(`/api/v1/jobs/${jobId}`);
  },

  getDashboard(): Promise<DashboardStats> {
    return request("/api/v1/dashboard");
  },

  createMeasurement(
    modelId: number,
    points: number[][],
    measurementType: "distance" | "angle",
  ): Promise<{ measurement: Measurement }> {
    return request(`/api/v1/models/${modelId}/measurements`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ points, measurement_type: measurementType }),
    });
  },

  meshUrl(modelId: number): string {
    return `${API_BASE}/api/v1/models/${modelId}/mesh`;
  },

  exportUrl(modelId: number, fmt: "stl" | "obj" | "glb"): string {
    return `${API_BASE}/api/v1/models/${modelId}/export/${fmt}`;
  },

  getVolumeInfo(id: number): Promise<VolumeInfo> {
    return request(`/api/v1/studies/${id}/volume`);
  },

  getMprSlice(
    id: number,
    plane: PlaneName,
    index: number,
    width?: number,
    level?: number,
  ): Promise<MprSlice> {
    const params = new URLSearchParams({ index: String(index) });
    if (width != null) params.set("width", String(width));
    if (level != null) params.set("level", String(level));
    return request(`/api/v1/studies/${id}/mpr/${plane}?${params.toString()}`);
  },

  getCoordinates(id: number, x: number, y: number, z: number): Promise<CoordinateInfo> {
    const params = new URLSearchParams({
      x: String(x),
      y: String(y),
      z: String(z),
    });
    return request(`/api/v1/studies/${id}/coordinates?${params.toString()}`);
  },

  listSegmentationModels(): Promise<SegmentationModelInfo[]> {
    return request("/api/v1/segmentation/models");
  },

  createSegmentationJob(studyId: number, modelId: string): Promise<SegmentationJobResponse> {
    return request("/api/v1/segmentation/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_id: modelId, study_id: studyId }),
    });
  },

  getSegmentationJob(jobId: string): Promise<SegmentationJobStatus> {
    return request(`/api/v1/segmentation/jobs/${jobId}`);
  },

  listSegmentations(studyId: number): Promise<{ results: SegmentationResult[] }> {
    return request(`/api/v1/studies/${studyId}/segmentations`);
  },

  getSegmentationResult(resultId: number): Promise<SegmentationResult> {
    return request(`/api/v1/segmentation/results/${resultId}`);
  },
};
