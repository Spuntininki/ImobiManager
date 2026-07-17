import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Unmount any rendered components between tests so the DOM stays isolated.
afterEach(() => {
  cleanup();
});