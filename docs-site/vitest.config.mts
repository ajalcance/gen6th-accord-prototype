// Vitest configuration for the docs-site tests.
// Mirrors the frontend's setup: `npm test` is a real gate (CI runs it via `npm test --if-present`),
// so a loader that would publish an internal document fails the merge — not just a reviewer.
// The loader reads the filesystem, so the tests run in Node, not a browser environment.
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
  },
});
