import type { BenchmarkReport } from "../../lib/persona-benchmark";
import { useBenchmarkReport } from "./use-benchmark-report";

export default function BenchmarkReportPanel() {
  const { report, error, busy, inspect } = useBenchmarkReport();
  return (
    <section
      className="benchmark-report"
      aria-label="Recognition benchmark evidence"
    >
      <h3>Recognition benchmark evidence</h3>
      <p className="help">
        Inspect an offline evaluator report. The file stays in this browser;
        supplied observations and claimed byte checks require independent
        review. Importing a report does not enable search.
      </p>
      <label>
        Choose benchmark report JSON
        <input
          type="file"
          accept=".json,application/json"
          onChange={(event) => void inspect(event.target.files?.[0])}
        />
      </label>
      {busy && <p role="status">Inspecting report…</p>}
      {error && (
        <p role="alert">
          Invalid or oversized benchmark report. Choose an accord-benchmark-v1
          report.
        </p>
      )}
      {!report && !busy && !error && (
        <p role="status">
          Recognition accuracy is unmeasured here. No benchmark report loaded.
        </p>
      )}
      {report && <ReportResults report={report} />}
    </section>
  );
}
function ReportResults({ report: r }: { report: BenchmarkReport }) {
  return (
    <div>
      <p role="status">Supplied observations · Human review required</p>
      <p>
        {r.model} / {r.revision} ·{" "}
        {r.role === "face" ? "Face representation" : "Whole-image baseline"}
      </p>
      <p>
        Corpus byte check reported:{" "}
        {r.corpus_binding === "bytes_checked"
          ? "Completed by evaluator"
          : "Not performed"}
        . Provider execution and permissions are not verified by this viewer.
      </p>
      <ReportMetrics report={r} />
      <CaseResults report={r} />
      <p className="help">
        Failed queries remain in recall denominators. Scored false-match rates
        exclude unscored attempts; a failed absent query cannot demonstrate safe
        rejection. A calibration maximum threshold is provisional and does not
        include the deployed search margin. Unscored queries can also result
        from failed references; total minus scored minus failed exposes that
        count.
      </p>
      <details>
        <summary>Input fingerprints</summary>
        <p>Manifest: {r.manifest_sha256}</p>
        <p>Observations: {r.observations_sha256}</p>
        <p>Calibration threshold: {r.threshold}</p>
      </details>
    </div>
  );
}
function ReportMetrics({ report: r }: { report: BenchmarkReport }) {
  return (
    <dl>
      <div>
        <dt>Held-out queries / failed queries / failed references</dt>
        <dd>
          {r.test_queries} / {r.failed_queries} / {r.failed_references}
        </dd>
      </div>
      <div>
        <dt>Recall at 1 / 3 / 5 (all known queries)</dt>
        <dd>
          {["1", "3", "5"]
            .map((k) => `${(r.recall[k] * 100).toFixed(1)}%`)
            .join(" / ")}
        </dd>
      </div>
      <div>
        <dt>Strong false matches</dt>
        <dd>{r.strong_false_matches}</dd>
      </div>
      <div>
        <dt>Latency p50 / p95 / max (all attempts)</dt>
        <dd>
          {r.latency_ms_p50} / {r.latency_ms_p95} / {r.latency_ms_max} ms
        </dd>
      </div>
      <div>
        <dt>Total reported cost</dt>
        <dd>
          {r.cost_usd_total === null
            ? `Unknown (${r.cost_unknown_observations} observations missing cost; $${r.cost_usd_known.toFixed(4)} known)`
            : `$${r.cost_usd_total.toFixed(4)}`}
        </dd>
      </div>
    </dl>
  );
}
function CaseResults({ report: r }: { report: BenchmarkReport }) {
  return (
    <div
      className="benchmark-table"
      tabIndex={0}
      role="region"
      aria-label="Scrollable benchmark case results"
    >
      <table>
        <caption>Held-out case denominators</caption>
        <thead>
          <tr>
            <th>Case</th>
            <th>Total</th>
            <th>Scored</th>
            <th>Failed</th>
            <th>Abstained</th>
            <th>False matches / scored</th>
            <th>Recall at 1 / 3 / 5</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(r.strata).map(([name, s]) => (
            <tr key={name}>
              <th scope="row">{name}</th>
              <td>{s.total}</td>
              <td>{s.scored}</td>
              <td>{s.failed}</td>
              <td>{s.abstained}</td>
              <td>
                {s.strong_false_matches} / {s.scored}
                {s.false_match_rate_scored === null
                  ? " (unmeasured)"
                  : ` (${(s.false_match_rate_scored * 100).toFixed(1)}%)`}
              </td>
              <td>
                {s.recall === null
                  ? "Not applicable"
                  : ["1", "3", "5"]
                      .map((k) => `${(s.recall![k] * 100).toFixed(1)}%`)
                      .join(" / ")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
