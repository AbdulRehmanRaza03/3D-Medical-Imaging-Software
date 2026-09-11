import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { ModelInfo } from "@/components/medical/ModelInfo";

describe("ModelInfo", () => {
  it("renders study metadata", () => {
    const metadata = {
      study_id: 1,
      study_uid: "uid",
      patient_id: null,
      modality: "CT",
      study_date: "20240101",
      series_description: "Axial",
      rows: 512,
      columns: 512,
      slice_count: 164,
      pixel_spacing: [0.68, 0.68],
      slice_thickness: 1.0,
      slice_spacing: 1.0,
      image_orientation: null,
      image_position: null,
      rescale_slope: null,
      rescale_intercept: null,
      physical_size: null,
      warnings: [],
    };
    render(<ModelInfo metadata={metadata as any} model={undefined} />);
    expect(screen.getByText("CT")).toBeInTheDocument();
    expect(screen.getByText("164")).toBeInTheDocument();
  });

  it("renders model statistics", () => {
    const model = {
      id: 1,
      study_id: 1,
      series_id: null,
      name: "Bone",
      method: "marching_cubes",
      threshold_hu: 300,
      vertices: 124520,
      triangles: 249018,
      bbox_min: null,
      bbox_max: null,
      physical_size: [100, 100, 80],
      status: "ready",
      created_at: "2024-01-01T00:00:00",
    };
    render(<ModelInfo metadata={undefined} model={model as any} />);
    expect(screen.getByText("124,520")).toBeInTheDocument();
    expect(screen.getByText("249,018")).toBeInTheDocument();
    expect(screen.getByText(/marching cubes/i)).toBeInTheDocument();
  });
});
