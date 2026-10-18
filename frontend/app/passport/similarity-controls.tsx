import type { SimilarityFlow } from "./use-similarity-flow";
import { ReadFeedback } from "./saved-record";
import SimilarityPreview from "./similarity-preview";

const readinessText = {
  processing_unavailable: "Face similarity processing is not connected.",
  calibration_required:
    "A reviewed benchmark and calibration policy are required.",
  calibration_expired: "The calibration policy needs renewed review.",
  ready: "Private studio similarity search is ready under the reviewed policy.",
};

export function SimilarityControls({ flow }: { flow: SimilarityFlow }) {
  const pending =
    flow.preparation.state.phase === "loading" ||
    flow.results.state.phase === "loading";
  const ready =
    flow.readiness.state.phase === "ready" &&
    flow.readiness.state.value.state === "ready";
  return (
    <>
      <ReadinessControls flow={flow} pending={pending} />
      {pending && (
        <p className="help">
          Stopping the browser request may leave server processing in flight.
          Clear the query to prevent its use.
        </p>
      )}
      <div className="photo-actions">
        <QueryPicker flow={flow} disabled={!ready || pending} />
        <button
          className="secondary"
          disabled={!ready || !flow.file || pending || !!flow.receipt}
          onClick={flow.prepare}
        >
          Prepare face query
        </button>
        <button className="secondary" onClick={flow.clear}>
          Clear face query
        </button>
      </div>
      <p className="help">
        PNG or JPEG · up to 10 MB · encrypted query expires within ten minutes
        {flow.file ? ` · ${flow.file.name}` : ""}
      </p>
      {flow.message && <p role="alert">{flow.message}</p>}
      {flow.cleanup.status && <p role="status">{flow.cleanup.status}</p>}
      {flow.cleanup.status.startsWith("Server clearing is unconfirmed") && (
        <button className="secondary" onClick={() => void flow.cleanup.clear()}>
          Retry server clearing
        </button>
      )}
      <ReadFeedback
        state={flow.preparation.state}
        retry={() => void flow.preparation.query.retry()}
        cancel={() => flow.preparation.query.cancel()}
      />
      {flow.receipt && flow.gateway && <PreparedQuery flow={flow} />}
    </>
  );
}

function QueryPicker({
  flow,
  disabled,
}: {
  flow: SimilarityFlow;
  disabled: boolean;
}) {
  return (
    <label className="photo-picker">
      Choose face query image
      <input
        type="file"
        accept="image/png,image/jpeg"
        disabled={disabled}
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null;
          flow.clear();
          flow.setMessage("");
          event.target.value = "";
          if (
            file &&
            ["image/png", "image/jpeg"].includes(file.type) &&
            file.size > 0 &&
            file.size <= 10485760
          )
            flow.setFile(file);
          else if (file)
            flow.setMessage("Choose a valid PNG or JPEG within 10 MB.");
        }}
      />
    </label>
  );
}

function ReadinessControls({
  flow,
  pending,
}: {
  flow: SimilarityFlow;
  pending: boolean;
}) {
  return (
    <>
      <button
        className="secondary"
        disabled={!flow.gateway || pending}
        onClick={() => {
          if (flow.gateway)
            void flow.readiness.query.run((signal) =>
              flow.gateway!.readiness(signal),
            );
        }}
      >
        Check search readiness
      </button>
      <ReadFeedback
        state={flow.readiness.state}
        retry={() => void flow.readiness.query.retry()}
        cancel={() => flow.readiness.query.cancel()}
      />
      {flow.readiness.state.phase === "ready" && (
        <p role="status">{readinessText[flow.readiness.state.value.state]}</p>
      )}
    </>
  );
}

function PreparedQuery({ flow }: { flow: SimilarityFlow }) {
  const r = flow.receipt!;
  return (
    <section aria-label="Select query face">
      <SimilarityPreview
        gateway={flow.gateway!}
        receipt={r}
        ready={flow.setPreviewReady}
        denied={flow.invalidate}
      />
      <p className="help">
        Query {r.query_id} · {r.detector} · expires {r.expires_at}
      </p>
      {r.state === "no_face" ? (
        <p role="status">No face detected. Prepare another image.</p>
      ) : (
        <FaceSelection flow={flow} />
      )}
    </section>
  );
}

function FaceSelection({ flow }: { flow: SimilarityFlow }) {
  const pending = flow.results.state.phase === "loading";
  return (
    <>
      <fieldset disabled={pending || !flow.previewReady}>
        <legend>Choose the intended face</legend>
        {flow.receipt!.faces.map((f) => (
          <label key={f.index}>
            <input
              type="radio"
              name="query-face"
              checked={flow.face === f.index}
              onChange={() => {
                flow.setFace(f.index);
                flow.setConfirmed(false);
                flow.results.query.clear();
              }}
            />{" "}
            Face {f.index + 1} · detection confidence {f.confidence.toFixed(3)}
          </label>
        ))}
      </fieldset>
      <label>
        <input
          type="checkbox"
          disabled={flow.face === null || pending || !flow.previewReady}
          checked={flow.confirmed}
          onChange={(e) => flow.setConfirmed(e.target.checked)}
        />{" "}
        I confirm the selected face is the intended performer.
      </label>
      <QueryScope flow={flow} />
      <button
        className="secondary"
        disabled={
          pending || flow.face === null || !flow.confirmed || !flow.previewReady
        }
        onClick={flow.search}
      >
        Search approved references
      </button>
    </>
  );
}

function QueryScope({ flow }: { flow: SimilarityFlow }) {
  return (
    <label>
      Studio scope{" "}
      <select
        aria-label="Similarity scope"
        value={flow.scope}
        disabled={flow.results.state.phase === "loading"}
        onChange={(e) => {
          flow.setScope(e.target.value as "current" | "history");
          flow.results.query.clear();
        }}
      >
        <option value="current">Current approved references</option>
        <option value="history">Approved reference history</option>
      </select>
      <span className="help"> Public and web discovery are future work.</span>
    </label>
  );
}
