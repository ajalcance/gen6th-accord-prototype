import Portrait from "./portrait";
import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";
import { SCAN_PHASES } from "./console-fixtures";
import PaletteComparison from "./palette-comparison";

export function ScanWorkspace(props: StudioState) {
  return (
    <section className="panel investigation-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">02 / ANALYSIS WORKSPACE</p>
          <h2>Artifact inspection</h2>
        </div>
        <span className="status">Fixture analysis</span>
      </div>
      <p className="help">
        One original vector study in three palettes. This is a scripted
        comparison, not AI analysis, a copying probability or a facial identity
        check.
      </p>
      {props.analysis === "ready" ? (
        <details className="completed-source">
          <summary>
            Inspect source illustration · fixture-v{props.revision}
          </summary>
          <ScanCanvas {...props} />
        </details>
      ) : (
        <ScanCanvas {...props} />
      )}
      <ScanProgress {...props} />
      <ScanControls {...props} />
    </section>
  );
}

function ScanCanvas(props: StudioState) {
  const running = props.analysis === "running";
  return (
    <div
      className={`scan-canvas ${running ? "is-scanning" : ""} ${props.analysis === "ready" ? "is-ready" : ""}`}
      data-phase={props.phase}
    >
      <div className="canvas-label">
        <span>
          <span className="demo-dot" />
          {running ? "SIMULATION IN PROGRESS" : "CANONICAL STUDY"}
        </span>
        <span>fixture-v{props.revision}</span>
      </div>
      <div className="scan-artifact">
        <Portrait variant={props.variant} />
        <div className="scan-grid" aria-hidden="true" />
        {running && <div className="scan-sweep" aria-hidden="true" />}
        <div className="scan-frame" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
        {running && props.phase > 0 && (
          <div className="scan-regions" aria-hidden="true">
            <span>COMPOSITION</span>
            <span>PALETTE</span>
          </div>
        )}
      </div>
      <div className="canvas-caption">
        <Icon name="file" />
        <span>
          character-study.svg
          <small>Illustrative image regions · no biometric processing</small>
        </span>
        <span className="source-label">SOURCE 01</span>
      </div>
    </div>
  );
}

function ScanProgress(props: StudioState) {
  const text =
    props.analysis === "ready"
      ? "Demo scenario loaded · one palette derivative and two evidence gaps"
      : props.analysis === "error"
        ? "Simulated interruption. Your draft is preserved."
        : props.analysis === "cancelled"
          ? "Simulation cancelled. Your draft is preserved."
          : props.analysis === "running"
            ? SCAN_PHASES[Math.min(props.phase, 4)]
            : "Ready to explore the review scenario";
  return (
    <div className="scan-progress">
      <div className="scan-progress-heading">
        <span role="status" aria-live="polite">
          {text}
        </span>
        <span className="muted">
          {props.analysis === "ready" ? "5" : props.phase} / 5 stages
        </span>
      </div>
      <ScanStages {...props} text={text} />
    </div>
  );
}

function ScanControls(props: StudioState) {
  return (
    <div className="scan-actions">
      <div className="button-row">
        <button
          className={props.analysis === "ready" ? "secondary" : "primary"}
          disabled={props.analysis === "running" || !props.canReview}
          onClick={() => props.setAnalysis("running")}
        >
          <Icon name="scan" />
          {props.analysis === "error" || props.analysis === "cancelled"
            ? "Retry demo"
            : "Run demo scenario"}
        </button>
        {props.analysis === "running" && (
          <button
            className="secondary"
            onClick={() => props.setAnalysis("cancelled")}
          >
            Cancel simulation
          </button>
        )}
      </div>
      <details className="scenario-controls">
        <summary>Scenario controls</summary>
        <p className="help">
          Demo-only recovery exercise. No server job is affected.
        </p>
        <button
          className="text-button"
          onClick={() => props.setAnalysis("error")}
        >
          Simulate interruption
        </button>
      </details>
    </div>
  );
}

export function ReferenceResults(props: StudioState) {
  return (
    <section className="panel reference-panel">
      <div className="panel-heading">
        <h3>Reference workspace</h3>
        <span className="status">
          {props.analysis === "ready"
            ? "Scenario ready"
            : "Waiting for scenario"}
        </span>
      </div>
      {props.analysis !== "ready" ? (
        <div className="reference-empty">
          <Icon name="search" size={26} />
          <p>
            Run the scenario to inspect an altered palette and an unrelated
            control.
          </p>
        </div>
      ) : (
        <>
          <ReferenceCards {...props} />
          {props.candidate && <PaletteComparison {...props} />}
        </>
      )}
    </section>
  );
}

function ScanStages(props: StudioState & { text: string }) {
  return (
    <div
      role="progressbar"
      aria-label="Fixture analysis stages"
      aria-valuemin={0}
      aria-valuemax={5}
      aria-valuenow={props.phase}
      aria-valuetext={props.text}
      className="stage-track"
    >
      {SCAN_PHASES.map((title, index) => (
        <span
          key={title}
          className={
            index < props.phase
              ? "complete"
              : props.analysis === "running" && index === props.phase
                ? "active"
                : ""
          }
          title={title}
        >
          <span>
            {index < props.phase ? "✓" : String(index + 1).padStart(2, "0")}
          </span>
          <small>{title}</small>
        </span>
      ))}
    </div>
  );
}

function ReferenceCards(props: StudioState) {
  return (
    <div className="reference-filmstrip">
      <button
        className={`reference-card ${props.candidate ? "selected" : ""}`}
        aria-expanded={props.candidate}
        onClick={() => props.setCandidate(!props.candidate)}
      >
        <Portrait variant={(props.variant + 1) % 3} />
        <span>
          Palette derivative
          <small>
            {props.candidate ? "Close comparison" : "Inspect candidate"}
          </small>
        </span>
      </button>
      <details className="reference-card reference-control">
        <summary>Unrelated control · inspect reference</summary>
        <svg viewBox="0 0 160 120" aria-hidden="true">
          <rect width="160" height="120" fill="#304757" />
          <circle cx="70" cy="60" r="40" fill="#edc595" />
          <path d="M85 20L145 100H25Z" fill="#9098c3" />
        </svg>
        <p className="help">
          Original geometric fixture, geometric-control-01. No shared portrait
          drawing; no computed similarity verdict. A real benchmark must measure
          incorrect retrieval.
        </p>
      </details>
      <div className="reference-context">
        <span className="status warning">2 evidence gaps</span>
        <p>
          References describe a controlled scenario. They are not internet-wide
          results.
        </p>
        <button className="text-button" onClick={() => props.ask("candidate")}>
          Explain this finding
          <Icon name="arrow" />
        </button>
      </div>
    </div>
  );
}
