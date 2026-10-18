import { useEffect, useMemo } from "react";
import type {
  CaptureMetadata,
  CaptureProfile,
  CaptureQuery,
} from "../../lib/persona-captures";
import { requireContract } from "../../lib/persona-validation";
import { useSavedSource, type SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";
import { ReadFeedback } from "./saved-record";
import CopyReference from "./copy-reference";

export function useCaptureProfile(
  source: SavedPersonaSource,
  command: CaptureQuery,
  digest?: string,
  denied?: () => void,
) {
  const { query, state } = usePersonaQuery<CaptureProfile>();
  const gateway = source.captures;
  useEffect(() => {
    if (!gateway || gateway.workspaceId !== source.workspaceId) return;
    void query.run(async (signal) => {
      const profile = await gateway.query(command, signal);
      requireContract(
        !digest || !profile.capture || profile.capture.source_sha256 === digest,
      );
      return profile;
    });
    return () => query.stop();
  }, [gateway, source.workspaceId, command, digest, query]);
  useEffect(() => {
    if (state.phase === "denied") denied?.();
  }, [state.phase, denied]);
  return {
    query,
    state,
    available: gateway?.workspaceId === source.workspaceId,
  };
}

export function CaptureSummary({
  capture,
}: {
  capture: CaptureMetadata | null;
}) {
  return (
    <section aria-label="Analysis capture">
      <p role="status">
        {capture
          ? "Analysis image prepared"
          : "Analysis image not prepared for this portrait"}
      </p>
      <p className="help">
        Capture preparation is separate from face processing and recognition.
      </p>
      {capture && (
        <p className="capture-pixels">
          Source {capture.source_width} × {capture.source_height} · prepared{" "}
          {capture.width} × {capture.height} pixels
        </p>
      )}
      {capture && <CaptureProvenance capture={capture} />}
    </section>
  );
}

function CaptureProvenance({ capture }: { capture: CaptureMetadata }) {
  const fields: [string, string | number][] = [
    ["Source pixels", `${capture.source_width} × ${capture.source_height}`],
    ["Analysis pixels", `${capture.width} × ${capture.height}`],
    ["Source orientation", capture.orientation],
    [
      "Processing recipe",
      `${capture.recipe} · Pillow ${capture.decoder_version}`,
    ],
    ["Source digest", capture.source_sha256],
    ["Analysis digest", capture.sha256],
  ];
  return (
    <details>
      <summary>Inspect capture provenance</summary>
      <dl className="saved-fields">
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>
              {label.endsWith("digest") ? (
                <CopyReference label={String(label)} value={String(value)} />
              ) : (
                value
              )}
            </dd>
          </div>
        ))}
        <div>
          <dt>Prepared at</dt>
          <dd>
            <time dateTime={capture.recorded_at}>{capture.recorded_at}</time>
          </dd>
        </div>
      </dl>
    </details>
  );
}

export function StagedCaptureStatus({
  id,
  digest,
}: {
  id: string;
  digest?: string;
}) {
  const source = useSavedSource();
  if (!source) return null;
  return (
    <StagedStatus
      key={`${source.workspaceId}:${source.sessionKey}:${id}`}
      source={source}
      id={id}
      digest={digest}
    />
  );
}
function StagedStatus({
  source,
  id,
  digest,
}: {
  source: SavedPersonaSource;
  id: string;
  digest?: string;
}) {
  const command = useMemo(() => ({ upload_id: id, version_id: null }), [id]);
  const { query, state, available } = useCaptureProfile(
    source,
    command,
    digest,
  );
  if (!available)
    return <p className="help">Analysis capture status is unavailable.</p>;
  return (
    <>
      <ReadFeedback
        state={state}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {state.phase === "ready" && (
        <CaptureSummary capture={state.value.capture} />
      )}
    </>
  );
}
