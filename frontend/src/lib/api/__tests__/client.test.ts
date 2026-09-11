import { describe, it, expect } from "vitest";

import { api, ApiError } from "@/lib/api/client";

describe("ApiError", () => {
  it("carries status and code", () => {
    const err = new ApiError("not valid", 422, "invalid_dicom");
    expect(err.status).toBe(422);
    expect(err.code).toBe("invalid_dicom");
  });
});

describe("api URL builders", () => {
  it("builds export URLs", () => {
    expect(api.exportUrl(5, "stl")).toContain("/export/stl");
    expect(api.exportUrl(5, "obj")).toContain("/export/obj");
    expect(api.exportUrl(5, "glb")).toContain("/export/glb");
  });

  it("builds mesh URL", () => {
    expect(api.meshUrl(7)).toContain("/models/7/mesh");
  });
});
