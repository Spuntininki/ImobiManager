import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

describe("test harness smoke", () => {
  it("renders into jsdom and applies jest-dom matchers", () => {
    render(<button aria-label="action">Click</button>);
    const button = screen.getByRole("button", { name: "action" });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent("Click");
  });
});