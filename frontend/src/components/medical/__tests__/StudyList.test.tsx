import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { StudyList } from "@/components/medical/StudyList";

describe("StudyList", () => {
  it("shows empty state when no studies", () => {
    render(<StudyList studies={[]} />);
    expect(screen.getByText(/No imaging studies yet/i)).toBeInTheDocument();
  });

  it("renders study rows with status", () => {
    const studies = [
      {
        id: 1,
        study_uid: "uid",
        name: "Test Study",
        modality: "CT",
        status: "ready",
        slice_count: 164,
        series_count: 1,
        study_date: "20240101",
        created_at: "2024-01-01T00:00:00",
        updated_at: "2024-01-01T00:00:00",
        error_message: null,
      },
    ];
    render(<StudyList studies={studies as any} />);
    expect(screen.getByText("Test Study")).toBeInTheDocument();
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("164")).toBeInTheDocument();
  });

  it("shows a failed status style", () => {
    const studies = [
      {
        id: 2,
        study_uid: "uid",
        name: "Failed Study",
        modality: "CT",
        status: "failed",
        slice_count: 0,
        series_count: 0,
        study_date: null,
        created_at: "2024-01-01T00:00:00",
        updated_at: "2024-01-01T00:00:00",
        error_message: "boom",
      },
    ];
    render(<StudyList studies={studies as any} />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });
});
