import { useEffect, useState } from "react";
import type {
  InvestigationResult,
  InvestigationCommand,
} from "../../lib/persona-investigation-contracts";
import type {
  QueryReceipt,
  SimilarityCandidate,
  SimilarityPage,
} from "../../lib/persona-similarity-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";
import { ReadFeedback } from "./saved-record";
import InvestigationFindings from "./investigation-findings";
import { IndependentReview } from "./investigation-history";
import RequestInvestigationReview from "./investigation-review-request";

type Props = {
  source: SavedPersonaSource;
  candidate: SimilarityCandidate;
  receipt: QueryReceipt;
  page: SimilarityPage;
  denied: () => void;
};
function useInvestigation(props: Props) {
  const { denied } = props;
  const readiness = usePersonaQuery<"ready" | "processing_unavailable">();
  const findings = usePersonaQuery<InvestigationResult>();
  const [note, setNote] = useState("");
  const [retain, setRetain] = useState(false);
  useEffect(() => {
    if (
      [readiness.state.phase, findings.state.phase].some(
        (p) => p === "denied" || p === "expired",
      )
    )
      denied();
  }, [readiness.state.phase, findings.state.phase, denied]);
  const generate = () => {
    const command: InvestigationCommand = {
      request_id: crypto.randomUUID(),
      query_id: props.receipt.query_id,
      face_index: props.page.face_index,
      scope: props.page.scope,
      version_id: props.candidate.version.version_id,
      portrait_id: props.candidate.portrait_id,
      generation_id: props.candidate.generation_id,
      source_note: note.trim(),
      retain_findings: true,
    };
    void findings.query.run((signal) =>
      props.source.investigations!.generate(command, signal),
    );
  };
  return { readiness, findings, note, setNote, retain, setRetain, generate };
}
export default function InvestigationPanel(props: Props) {
  const flow = useInvestigation(props);
  if (!props.source.investigations)
    return <p>Grounded investigation is unavailable on this connection.</p>;
  return (
    <section aria-label="Investigate supplied appearance">
      <h3>Investigate this appearance</h3>
      <p className="help">
        Compare this supplied image with the selected approved reference. The
        server refreshes search evidence before Gemini analysis. No web scanning
        or automatic reuse verdict.
      </p>
      <Availability flow={flow} source={props.source} />
      <InvestigationControls flow={flow} />
      <ReadFeedback
        state={flow.findings.state}
        retry={() => void flow.findings.query.retry()}
        cancel={() => flow.findings.query.cancel()}
      />
      {flow.findings.state.phase === "cancelled" && (
        <p>
          Server processing may finish and save the evidence packet. Retry the
          same intent or inspect this version’s analysis history.
        </p>
      )}
      {flow.findings.state.phase === "ready" && (
        <>
          <InvestigationFindings result={flow.findings.state.value} />
          <RequestInvestigationReview
            source={props.source}
            packet={flow.findings.state.value}
            denied={props.denied}
          />
          <IndependentReview
            source={props.source}
            version={props.candidate.version}
            denied={props.denied}
          />
        </>
      )}
    </section>
  );
}
type Flow = ReturnType<typeof useInvestigation>;
function Availability({
  flow,
  source,
}: {
  flow: Flow;
  source: SavedPersonaSource;
}) {
  return (
    <>
      <button
        className="secondary"
        disabled={flow.readiness.state.phase === "loading"}
        onClick={() =>
          void flow.readiness.query.run((signal) =>
            source.investigations!.readiness(signal),
          )
        }
      >
        Check investigation availability
      </button>
      <ReadFeedback
        state={flow.readiness.state}
        retry={() => void flow.readiness.query.retry()}
        cancel={() => flow.readiness.query.cancel()}
      />
      {flow.readiness.state.phase === "ready" &&
        flow.readiness.state.value !== "ready" && (
          <p role="status">
            Investigation processing is unavailable. Reviewed model, storage and
            calibration setup is required.
          </p>
        )}
    </>
  );
}
function InvestigationControls({
  flow,
}: {
  flow: ReturnType<typeof useInvestigation>;
}) {
  const frozen = flow.findings.state.phase !== "idle";
  return (
    <>
      <EvidenceContext flow={flow} frozen={frozen} />
      <button
        className="primary"
        disabled={
          frozen ||
          !flow.retain ||
          !flow.note.trim() ||
          flow.readiness.state.phase !== "ready" ||
          flow.readiness.state.value !== "ready"
        }
        onClick={flow.generate}
      >
        Generate grounded findings
      </button>
      {frozen && flow.findings.state.phase !== "loading" && (
        <button
          className="secondary"
          onClick={() => flow.findings.query.clear()}
        >
          Clear analysis view for a new intent
        </button>
      )}
    </>
  );
}
function EvidenceContext({ flow, frozen }: { flow: Flow; frozen: boolean }) {
  return (
    <>
      <label>
        Where was this appearance supplied from?
        <textarea
          maxLength={500}
          placeholder="Describe the supplied source and the context to compare."
          value={flow.note}
          disabled={frozen}
          onChange={(event) => flow.setNote(event.target.value)}
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={flow.retain}
          disabled={frozen}
          onChange={(event) => flow.setRetain(event.target.checked)}
        />
        Save encrypted findings and provenance in this studio. Query images
        still expire.
      </label>
    </>
  );
}
