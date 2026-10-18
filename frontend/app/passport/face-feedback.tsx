import type { FaceResult } from "../../lib/persona-faces";
import type { FaceMutation } from "./face-state";

export function FaceMutationFeedback({ mutation }: { mutation: FaceMutation }) {
  return (
    <>
      {"message" in mutation.state && (
        <p role="alert">{mutation.state.message}</p>
      )}
      {mutation.mayRetry && (
        <button type="button" onClick={() => void mutation.retry()}>
          Retry same face request
        </button>
      )}
      {mutation.state.phase === "pending" && (
        <>
          <p role="status">Face processing is running…</p>
          <button type="button" onClick={mutation.cancel}>
            Stop waiting
          </button>
        </>
      )}
    </>
  );
}
export function FaceStatus({
  result,
  ready,
}: {
  result: FaceResult | null;
  ready: boolean;
}) {
  return (
    <>
      {!ready && (
        <p role="status">
          Processing provider is not configured. Stored results remain
          inspectable.
        </p>
      )}
      {!result && <p>Face detection has not run.</p>}
      {result?.faces.length === 10 && (
        <p>
          Detection is capped at ten faces. Use a closer reference if the
          performer is not shown.
        </p>
      )}
      {result?.state === "no_face" && (
        <p>No face detected. Approve a clearer reference to continue.</p>
      )}
      {result?.state === "quality_blocked" && (
        <p role="alert">
          Quality blocked:{" "}
          {result.reasons.map((r) => r.replaceAll("_", " ")).join(", ")}.
          Approve a clearer reference.
        </p>
      )}
      {result?.state === "represented" && (
        <p role="status">
          Face crop and whole-image representations stored. Retrieval
          calibration is pending.
        </p>
      )}
      <p className="help">
        Quality policy is provisional. Detection confidence does not establish
        performer identity.
      </p>
    </>
  );
}
export function FaceProvenance({ result }: { result: FaceResult }) {
  const r = result.representation;
  const fields = [
    ["Generation", result.generation_id],
    ["Recorded", result.recorded_at],
    ["Detector", result.detector],
    [
      "Selected face",
      result.selected === null ? "Awaiting selection" : result.selected + 1,
    ],
    ...(r
      ? [
          ["Embedding model", r.model],
          ["Provider revision", r.provider_revision],
          ["Dimensions", r.dimensions],
          ["Crop recipe", r.crop_recipe],
          ["Crop digest", r.crop_sha256],
          ["Quality policy", r.quality_policy],
        ]
      : []),
  ];
  return (
    <details>
      <summary>Face processing provenance</summary>
      <dl className="saved-fields">
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
