import { describe, it, expect } from "vitest";

import { useSegmentation } from "@/hooks/useSegmentation";

// This test verifies the hook module can be imported and the API surface exists.
// Full-behavior testing requires a mocked TanStack Query client, so we keep the
// scope focused on structural correctness.
describe("useSegmentation", () => {
  it("is a function", () => {
    expect(typeof useSegmentation).toBe("function");
  });
});
