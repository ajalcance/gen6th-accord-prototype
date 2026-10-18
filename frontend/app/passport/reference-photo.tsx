import FacePreview from "./face-preview";
import { useEffect, useRef } from "react";
import type { CaptureGateway } from "../../lib/persona-captures";
import { usePersonaQuery } from "./use-persona-query";
import { ReadFeedback } from "./saved-record";
import type { FaceResult } from "../../lib/persona-faces";

export default function ReferencePhoto({
  gateway,
  version,
  portrait,
  denied,
  faces,
}: {
  gateway: CaptureGateway;
  version: string;
  portrait: string;
  denied: () => void;
  faces?: FaceResult;
}) {
  const { query, state } = usePersonaQuery<string>();
  const url = useRef<string | null>(null);
  useEffect(() => {
    void query.run(async (signal) => {
      const blob = await gateway.thumbnail(version, portrait, signal);
      if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
      if (url.current) URL.revokeObjectURL(url.current);
      url.current = URL.createObjectURL(blob);
      return url.current;
    });
    return () => {
      query.stop();
      if (url.current) URL.revokeObjectURL(url.current);
      url.current = null;
    };
  }, [gateway, version, portrait, query]);
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  return (
    <>
      <ReadFeedback
        state={state}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {state.phase === "ready" && (
        <FacePreview url={state.value} faces={faces} />
      )}
    </>
  );
}
