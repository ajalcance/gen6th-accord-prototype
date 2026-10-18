import { useEffect, useMemo, useState } from "react";
import type { CaptureMetadata } from "../../lib/persona-captures";
import type { FaceProfile, FaceResult } from "../../lib/persona-faces";
import type { ReferenceProps } from "./saved-captures";
import { ReadFeedback } from "./saved-record";
import { usePersonaQuery } from "./use-persona-query";
import {
  useFaceMutation,
  resultReceipt,
  type FaceMutation,
} from "./face-state";
import FaceSelection from "./face-selection";
import DurableFaceJobs from "./durable-face-jobs";
import {
  FaceMutationFeedback,
  FaceProvenance,
  FaceStatus,
} from "./face-feedback";

export type FaceInspectionProps = ReferenceProps & { capture: CaptureMetadata };
export default function FaceInspection(props: FaceInspectionProps) {
  const [open, setOpen] = useState(false);
  if (
    !props.source.faces ||
    props.source.faces.workspaceId !== props.source.workspaceId ||
    !props.source.captures
  )
    return <p className="help">Face processing is not connected.</p>;
  return (
    <section aria-label="Face processing">
      <button
        type="button"
        className="secondary"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        {open ? "Close face processing" : "Inspect face processing"}
      </button>
      {open && (
        <FaceProcessing
          key={
            props.version.version_id +
            props.source.sessionKey +
            props.capture.portrait_id
          }
          {...props}
        />
      )}
    </section>
  );
}
function useFaceProcessing(props: FaceInspectionProps) {
  const { source, version, capture, denied } = props;
  const gateway = source.faces!;
  const subject = useMemo(
    () => ({
      version_id: version.version_id,
      portrait_id: capture.portrait_id,
    }),
    [version.version_id, capture.portrait_id],
  );
  const { query, state } = usePersonaQuery<FaceProfile>();
  const mutation = useFaceMutation(
    gateway,
    "faces:" + version.version_id + ":" + capture.portrait_id,
    denied,
  );
  useEffect(() => {
    void query.run((signal) => gateway.query(subject, signal));
    return () => query.stop();
  }, [query, gateway, subject]);
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  const profile = state.phase === "ready" ? state.value : null;
  const result = resultReceipt(mutation) ?? profile?.latest ?? null;
  return { query, state, mutation, profile, result };
}
function FaceProcessing(props: FaceInspectionProps) {
  const { query, state, mutation, profile, result } = useFaceProcessing(props);
  const { capture } = props;
  if (state.phase === "denied" || mutation.state.phase === "denied")
    return (
      <p role="alert">Face processing access was lost. Results were cleared.</p>
    );
  if (
    result &&
    (result.source_sha256 !== capture.sha256 ||
      result.width !== capture.width ||
      result.height !== capture.height)
  )
    return (
      <p role="alert">
        Face processing does not match this capture. No result is displayed.
      </p>
    );
  return (
    <>
      <ReadFeedback
        state={state}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      <FaceMutationFeedback mutation={mutation} />
      {profile &&
        (props.source.runtime ? (
          <DurableFaceJobs
            {...props}
            result={result}
            reloadResult={() => void query.retry()}
          />
        ) : (
          <FaceActions
            {...props}
            result={result}
            mutation={mutation}
            ready={profile.provider_ready}
          />
        ))}
      {result && <FaceProvenance result={result} />}
    </>
  );
}
type ActionProps = FaceInspectionProps & {
  result: FaceResult | null;
  mutation: FaceMutation;
  ready: boolean;
};
function FaceActions(props: ActionProps) {
  const { source, version, capture, result, mutation, ready } = props;
  const writable = source.writeGateway?.workspaceId === source.workspaceId;
  const blocked =
    mutation.requiresResolution || mutation.state.phase === "pending";
  function detect() {
    void mutation.submit({
      version_id: version.version_id,
      portrait_id: capture.portrait_id,
      request_id: crypto.randomUUID(),
      generation_id: null,
      face_index: null,
    });
  }
  return (
    <>
      <FaceStatus result={result} ready={ready} />
      {writable && (
        <button type="button" disabled={!ready || blocked} onClick={detect}>
          Run face detection
        </button>
      )}
      {result?.faces.length ? (
        <FaceSelection
          key={result.generation_id}
          {...props}
          result={result}
          disabled={!ready || !writable || blocked}
        />
      ) : null}
    </>
  );
}
