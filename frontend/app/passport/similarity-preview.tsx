import { useEffect, useRef } from "react";
import type { QueryReceipt } from "../../lib/persona-similarity-contracts";
import type { SimilarityGateway } from "../../lib/persona-similarity";
import { usePersonaQuery } from "./use-persona-query";
import { ReadFeedback } from "./saved-record";
import FacePreview from "./face-preview";

export default function SimilarityPreview({
  gateway,
  receipt,
  ready,
  denied,
}: {
  gateway: SimilarityGateway;
  receipt: QueryReceipt;
  ready: (value: boolean) => void;
  denied: () => void;
}) {
  const { query, state } = usePersonaQuery<string>();
  const url = useRef<string | null>(null);
  useEffect(() => {
    void query.run(async (signal) => {
      const blob = await gateway.thumbnail(receipt, signal);
      if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
      if (url.current) URL.revokeObjectURL(url.current);
      url.current = URL.createObjectURL(blob);
      return url.current;
    });
    return () => {
      query.stop();
      if (url.current) URL.revokeObjectURL(url.current);
      url.current = null;
      ready(false);
    };
  }, [gateway, receipt, query, ready]);
  useEffect(() => {
    ready(state.phase === "ready");
    if (state.phase === "denied" || state.phase === "expired") denied();
  }, [state.phase, ready, denied]);
  return (
    <div aria-label="Prepared query preview">
      <ReadFeedback
        state={state}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {state.phase === "ready" && (
        <FacePreview
          url={state.value}
          faces={receipt}
          alt="Prepared query image with numbered faces"
        />
      )}
    </div>
  );
}
