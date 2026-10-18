import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import BenchmarkReportPanel from "../app/passport/benchmark-report";
import { benchmarkFixture } from "./benchmark-fixture";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function choose(text: () => Promise<string>, size = 100) {
  fireEvent.change(screen.getByLabelText("Choose benchmark report JSON"), {
    target: { files: [{ size, text }] },
  });
}
it("keeps evidence local and labels imported reports as supplied observations", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  render(<BenchmarkReportPanel />);
  expect(screen.getByText(/Recognition accuracy is unmeasured/)).toBeDefined();
  choose(async () => JSON.stringify(benchmarkFixture));
  await screen.findByText(/Supplied observations · Human review required/);
  expect(
    screen.getByText(/Unknown \(1 observations missing cost/),
  ).toBeDefined();
  expect(screen.getByRole("table")).toBeDefined();
  expect(fetch).not.toHaveBeenCalled();
});
it("clears previous report when a new file is invalid", async () => {
  render(<BenchmarkReportPanel />);
  choose(async () => JSON.stringify(benchmarkFixture));
  await screen.findByText(/Supplied observations · Human review required/);
  choose(async () => "invalid json");
  await screen.findByRole("alert");
  expect(screen.queryByRole("table")).toBeNull();
});
it("bounds reads before loading oversized file contents", async () => {
  render(<BenchmarkReportPanel />);
  const read = vi.fn();
  choose(read, 16 * 1024 * 1024 + 1);
  await screen.findByRole("alert");
  expect(read).not.toHaveBeenCalled();
});
it("ignores stale file completion after replacement", async () => {
  render(<BenchmarkReportPanel />);
  let resolve!: (value: string) => void;
  choose(
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  choose(async () =>
    JSON.stringify({ ...benchmarkFixture, revision: "latest" }),
  );
  await screen.findByText(/synthetic-fixture \/ latest/);
  resolve(JSON.stringify(benchmarkFixture));
  await Promise.resolve();
  expect(screen.queryByText(/synthetic-fixture \/ fixture-only/)).toBeNull();
});
