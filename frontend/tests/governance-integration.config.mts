/** Additional local integration suite. Requires the installed backend .venv and Node 22. */
import { defineConfig } from "vitest/config";
import frontend from "../vitest.config.mjs";

export default defineConfig({
  ...frontend,
  test: { ...frontend.test, include: ["tests/**/*.integration.tsx"] },
});
