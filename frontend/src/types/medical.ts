/** Shared medical/imaging type definitions matching the backend Pydantic schemas. */

export type StudyStatus = "uploaded" | "processing" | "ready" | "failed";
export type JobStatus = "queued" | "processing" | "completed" | "failed";

export interface Study {
  id: number;
  study_uid: string;
  name: string;
  modality: string | null;
  status: StudyStatus;
  slice_count: number;
  series_count: number;
  study_date: string | null;
  created_at: string;
  updated_at: string;
  error_message: string | null;
}

export interface SeriesInfo {
  id: number;
  series_uid: string;
  series_number: number | null;
  description: string | null;
  modality: string | null;
  rows: number | null;
  columns: number | null;
  slice_count: number;
  pixel_spacing_x: number | null;
  pixel_spacing_y: number | null;
  slice_thickness: number | null;
  slice_spacing: number | null;
  image_orientation: string | null;
  image_position: string | null;
  is_selected: boolean;
  warnings: string | null;
}

export interface StudyDetail extends Study {
  series: SeriesInfo[];
}

export interface UploadResult {
  study: Study;
  series_detected: number;
  warnings: string[];
}

export interface Metadata {
  study_id: number;
  study_uid: string;
  patient_id: string | null;
  modality: string | null;
  study_date: string | null;
  series_description: string | null;
  rows: number | null;
  columns: number | null;
  slice_count: number;
  pixel_spacing: number[] | null;
  slice_thickness: number | null;
  slice_spacing: number | null;
  image_orientation: number[] | null;
  image_position: number[] | null;
  rescale_slope: number | null;
  rescale_intercept: number | null;
  physical_size: number[] | null;
  warnings: string[];
}

export interface SliceInfo {
  index: number;
  total: number;
  rows: number;
  columns: number;
  hu_min: number | null;
  hu_max: number | null;
}

export interface SliceResponse extends SliceInfo {
  width: number;
  level: number;
  image_base64: string;
}

export interface Model {
  id: number;
  study_id: number;
  series_id: number | null;
  name: string;
  method: string;
  threshold_hu: number;
  vertices: number;
  triangles: number;
  bbox_min: number[] | null;
  bbox_max: number[] | null;
  physical_size: number[] | null;
  status: string;
  created_at: string;
}

export interface Job {
  id: string;
  study_id: number;
  task_type: string;
  status: JobStatus;
  progress: number;
  message: string | null;
  error: string | null;
  result_model_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface Measurement {
  id: number;
  model_id: number;
  measurement_type: "distance" | "angle";
  value: number;
  unit: string;
  points: number[][];
  created_at: string;
}

export interface DashboardStats {
  total_studies: number;
  processed_studies: number;
  models_generated: number;
  recent_studies: Study[];
  processing_jobs: Job[];
}

export interface ReconstructRequest {
  threshold_hu: number;
  series_id?: number | null;
  method?: "marching_cubes";
  remove_small_components?: boolean;
  min_component_fraction?: number;
  smoothing_iterations?: number;
}

export interface ErrorResponse {
  detail: string;
  code: string | null;
}

// --- Phase 3: AI Segmentation ---
export interface SegmentationModelInfo {
  id: string;
  name: string;
  version: string;
  task: string;
  labels: string[];
  framework: string;
  target_spacing: number[] | null;
  checkpoint_path: string | null;
  checkpoint_available: boolean;
}

export interface SegmentationJobResponse {
  job_id: string;
  status: string;
}

export interface SegmentationLabelOut {
  id: number;
  name: string;
  color: string;
  voxel_count: number;
  volume_cm3: number;
  bbox_min: number[] | null;
  bbox_max: number[] | null;
  centroid: number[] | null;
}

export interface SegmentationResult {
  id: number;
  study_id: number;
  model_id: string;
  model_version: string;
  status: string;
  created_at: string;
  processing_duration_sec: number | null;
  device: string | null;
  labels: SegmentationLabelOut[];
  error: string | null;
}

export interface SegmentationJobStatus {
  id: string;
  study_id: number;
  task_type: string;
  status: string;
  progress: number;
  message: string | null;
  error: string | null;
  result_id: number | null;
}

// --- Phase 2: MPR ---
export type PlaneName = "axial" | "coronal" | "sagittal";

export interface VolumeInfo {
  shape: [number, number, number]; // depth, height, width
  dimensions: [number, number, number]; // width, height, depth
  spacing: [number, number, number]; // sx, sy, sz
  origin: [number, number, number];
  direction: number[]; // 9-element row-major
  hu_min: number;
  hu_max: number;
}

export interface MprSlice {
  plane: PlaneName;
  index: number;
  total: number;
  width: number;
  level: number;
  rows: number;
  columns: number;
  physical_width: number;
  physical_height: number;
  image_base64: string;
}

export interface CoordinateInfo {
  voxel: [number, number, number]; // fractional x,y,z
  index: [number, number, number]; // integer x,y,z = column,row,slice
  clamped_index: [number, number, number];
  world: [number, number, number];
  hu: number;
  in_bounds: boolean;
}

export interface VoxelInfo {
  index: [number, number, number];
  world: [number, number, number];
  hu: number;
}
