import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { WindowLevelControls } from "@/components/medical/WindowLevelControls";

describe("WindowLevelControls", () => {
  it("renders presets and calls handlers", () => {
    const onWidth = vi.fn();
    const onLevel = vi.fn();
    render(
      <WindowLevelControls
        width={400}
        level={40}
        onWidthChange={onWidth}
        onLevelChange={onLevel}
      />,
    );

    expect(screen.getByText("Bone")).toBeInTheDocument();
    expect(screen.getByText("Soft tissue")).toBeInTheDocument();
    expect(screen.getByText("Lung")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Bone"));
    expect(onWidth).toHaveBeenCalledWith(1800);
    expect(onLevel).toHaveBeenCalledWith(400);
  });

  it("updates window width via slider", () => {
    const onWidth = vi.fn();
    render(
      <WindowLevelControls
        width={400}
        level={40}
        onWidthChange={onWidth}
        onLevelChange={vi.fn()}
      />,
    );
    const slider = screen.getByLabelText("Window width");
    fireEvent.change(slider, { target: { value: "800" } });
    expect(onWidth).toHaveBeenCalledWith(800);
  });
});
