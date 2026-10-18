import { expect, it } from "vitest";
import { parseBenchmarkReport } from "../lib/persona-benchmark";
import { benchmarkFixture } from "./benchmark-fixture";

it("parses supplied evidence with unknown cost and explicit failed/scored denominators", () => {
  const report = parseBenchmarkReport(benchmarkFixture);
  expect(report.cost_usd_total).toBeNull();
  expect(report.strata.lookalike.false_match_rate_scored).toBeNull();
  expect(report.acceptance).toBe("human_review_required");
});
it.each([
  "extra",
  "false-cost",
  "bad-totals",
  "acceptance",
  "recall",
  "missing-cost",
  "latency",
])("rejects inconsistent report: %s", (change) => {
  const report = structuredClone(benchmarkFixture);
  const value: Record<string, unknown> = report;
  if (change === "extra") value.vector = [1, 0];
  if (change === "false-cost") value.cost_usd_total = 0;
  if (change === "bad-totals") value.test_queries = 4;
  if (change === "acceptance") value.acceptance = "approved";
  if (change === "recall") value.recall = { "1": 1, "3": 1, "5": 1 };
  if (change === "missing-cost") value.cost_unknown_observations = 0;
  if (change === "latency") value.latency_ms_p95 = 13;
  expect(() => parseBenchmarkReport(value)).toThrow();
});
