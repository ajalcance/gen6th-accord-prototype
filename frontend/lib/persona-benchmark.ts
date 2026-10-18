/** Local report inspection only; imported observations never enable calibrated search. */
import {
  choice,
  hex,
  integer,
  object,
  requireContract,
  text,
} from "./persona-validation";

export type BenchmarkStratum = {
  total: number;
  scored: number;
  failed: number;
  abstained: number;
  strong_false_matches: number;
  recall: Record<string, number> | null;
  false_match_rate_scored: number | null;
};
export type BenchmarkReport = {
  schema_version: "accord-benchmark-v1";
  evidence: "supplied_observations";
  corpus_binding: "unchecked" | "bytes_checked";
  manifest_sha256: string;
  observations_sha256: string;
  model: string;
  revision: string;
  role: "face" | "whole_image";
  threshold: number;
  threshold_source: "calibration_impostor_max";
  test_queries: number;
  known_queries: number;
  absent_queries: number;
  failed_queries: number;
  failed_references: number;
  recall: Record<string, number>;
  strong_false_matches: number;
  absent_false_match_rate: number;
  strata: Record<"regenerated" | "lookalike" | "absent", BenchmarkStratum>;
  latency_ms_p50: number;
  latency_ms_p95: number;
  latency_ms_max: number;
  cost_usd_total: number | null;
  cost_usd_known: number;
  cost_unknown_observations: number;
  acceptance: "human_review_required";
};

function number(value: unknown, min = 0, max = Infinity): number {
  requireContract(
    typeof value === "number" &&
      Number.isFinite(value) &&
      value >= min &&
      value <= max,
  );
  return value;
}
function recalls(value: unknown): Record<string, number> {
  const r = object(value, ["1", "3", "5"]);
  const result = {
    "1": number(r["1"], 0, 1),
    "3": number(r["3"], 0, 1),
    "5": number(r["5"], 0, 1),
  };
  requireContract(result["1"] <= result["3"] && result["3"] <= result["5"]);
  return result;
}
function parseStratum(value: unknown, absent: boolean): BenchmarkStratum {
  const r = object(value, [
    "total",
    "scored",
    "failed",
    "abstained",
    "strong_false_matches",
    "recall",
    "false_match_rate_scored",
  ]);
  const result: BenchmarkStratum = {
    total: integer(r.total),
    scored: integer(r.scored, 0),
    failed: integer(r.failed, 0),
    abstained: integer(r.abstained, 0),
    strong_false_matches: integer(r.strong_false_matches, 0),
    recall: r.recall === null ? null : recalls(r.recall),
    false_match_rate_scored:
      r.false_match_rate_scored === null
        ? null
        : number(r.false_match_rate_scored, 0, 1),
  };
  requireContract(
    result.scored + result.failed <= result.total &&
      result.abstained + result.strong_false_matches <= result.scored,
  );
  requireContract(absent === (result.recall === null));
  requireContract(
    result.scored === 0
      ? result.false_match_rate_scored === null
      : result.false_match_rate_scored ===
          result.strong_false_matches / result.scored,
  );
  return result;
}
const REPORT_KEYS = [
  "schema_version",
  "evidence",
  "corpus_binding",
  "manifest_sha256",
  "observations_sha256",
  "model",
  "revision",
  "role",
  "threshold",
  "threshold_source",
  "test_queries",
  "known_queries",
  "absent_queries",
  "failed_queries",
  "failed_references",
  "recall",
  "strong_false_matches",
  "absent_false_match_rate",
  "strata",
  "latency_ms_p50",
  "latency_ms_p95",
  "latency_ms_max",
  "cost_usd_total",
  "cost_usd_known",
  "cost_unknown_observations",
  "acceptance",
];
function parseIdentity(r: Record<string, unknown>) {
  return {
    schema_version: choice(r.schema_version, ["accord-benchmark-v1"]),
    evidence: choice(r.evidence, ["supplied_observations"]),
    corpus_binding: choice(r.corpus_binding, ["unchecked", "bytes_checked"]),
    manifest_sha256: hex(r.manifest_sha256, 64),
    observations_sha256: hex(r.observations_sha256, 64),
    model: text(r.model, 160),
    revision: text(r.revision, 160),
    role: choice(r.role, ["face", "whole_image"]),
    threshold: number(r.threshold, -1, 1.0000000000000002),
    threshold_source: choice(r.threshold_source, ["calibration_impostor_max"]),
    acceptance: choice(r.acceptance, ["human_review_required"]),
  };
}
export function parseBenchmarkReport(value: unknown): BenchmarkReport {
  const r = object(value, REPORT_KEYS);
  const s = object(r.strata, ["regenerated", "lookalike", "absent"]);
  const result: BenchmarkReport = {
    ...parseIdentity(r),
    test_queries: integer(r.test_queries),
    known_queries: integer(r.known_queries),
    absent_queries: integer(r.absent_queries),
    failed_queries: integer(r.failed_queries, 0),
    failed_references: integer(r.failed_references, 0),
    recall: recalls(r.recall),
    strong_false_matches: integer(r.strong_false_matches, 0),
    absent_false_match_rate: number(r.absent_false_match_rate, 0, 1),
    strata: {
      regenerated: parseStratum(s.regenerated, false),
      lookalike: parseStratum(s.lookalike, false),
      absent: parseStratum(s.absent, true),
    },
    latency_ms_p50: number(r.latency_ms_p50),
    latency_ms_p95: number(r.latency_ms_p95),
    latency_ms_max: number(r.latency_ms_max),
    cost_usd_total: r.cost_usd_total === null ? null : number(r.cost_usd_total),
    cost_usd_known: number(r.cost_usd_known),
    cost_unknown_observations: integer(r.cost_unknown_observations, 0),
  };
  validateTotals(result);
  return result;
}
function validateTotals(r: BenchmarkReport) {
  const { regenerated: g, lookalike: l, absent: a } = r.strata;
  requireContract(
    r.test_queries <= 10000 &&
      r.test_queries === g.total + l.total + a.total &&
      r.known_queries === g.total + l.total &&
      r.absent_queries === a.total,
  );
  requireContract(
    r.failed_queries === g.failed + l.failed + a.failed &&
      r.strong_false_matches ===
        g.strong_false_matches +
          l.strong_false_matches +
          a.strong_false_matches,
  );
  requireContract(
    r.absent_false_match_rate === a.strong_false_matches / a.total,
  );
  for (const k of ["1", "3", "5"])
    requireContract(
      Math.abs(
        r.recall[k] -
          (g.recall![k] * g.total + l.recall![k] * l.total) / r.known_queries,
      ) < 1e-12,
    );
  requireContract(
    r.latency_ms_p50 <= r.latency_ms_p95 &&
      r.latency_ms_p95 <= r.latency_ms_max,
  );
  requireContract(
    r.cost_unknown_observations > 0
      ? r.cost_usd_total === null
      : r.cost_usd_total === r.cost_usd_known,
  );
}
