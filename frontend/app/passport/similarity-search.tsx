import { useState } from "react";
import type {
  SimilarityCandidate,
  SimilarityPage,
  QueryReceipt,
} from "../../lib/persona-similarity-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { useSimilarityFlow } from "./use-similarity-flow";
import { SimilarityControls } from "./similarity-controls";
import { ReadFeedback } from "./saved-record";
import SimilarityComparison from "./similarity-comparison";

export default function SimilaritySearch({
  source,
  expanded = false,
}: {
  source: SavedPersonaSource;
  expanded?: boolean;
}) {
  const flow = useSimilarityFlow(source);
  return (
    <details
      className={`panel portrait-search${expanded ? " search-expanded" : ""}`}
      open={expanded || undefined}
    >
      <summary>Search by face similarity</summary>
      <p className="help">
        Prepare an image, confirm a detected face, then compare approved
        references in this studio. Query images do not become registered
        portraits. Similarity supports human review and does not establish
        identity or rights.
      </p>
      <SimilarityControls flow={flow} />
      <ReadFeedback
        state={flow.results.state}
        retry={() => void flow.results.query.retry()}
        cancel={() => flow.results.query.cancel()}
      />
      {flow.results.state.phase === "ready" && flow.receipt && (
        <ResultsAndComparison
          key={flow.results.state.value.request_id}
          page={flow.results.state.value}
          source={source}
          receipt={flow.receipt}
          denied={flow.invalidate}
        />
      )}
    </details>
  );
}

function ResultsAndComparison({
  page,
  source,
  receipt,
  denied,
}: {
  page: SimilarityPage;
  source: SavedPersonaSource;
  receipt: QueryReceipt;
  denied: () => void;
}) {
  const [selected, setSelected] = useState<SimilarityCandidate | null>(null);
  return (
    <>
      <SimilarityResults page={page} select={setSelected} />
      {selected && (
        <SimilarityComparison
          key={selected.generation_id}
          source={source}
          candidate={selected}
          query={receipt}
          scope={page.scope}
          page={page}
          denied={denied}
        />
      )}
    </>
  );
}

const resultText = {
  candidate_review: "Candidates require human comparison.",
  no_confident_match: "No confident match under the reviewed policy.",
  empty_catalogue: "No approved references in this scope.",
  no_compatible_references:
    "No references are compatible with this query and calibration.",
  quality_blocked:
    "The selected face does not meet the capture quality policy.",
};

function SimilarityResults({
  page,
  select,
}: {
  page: SimilarityPage;
  select: (value: SimilarityCandidate) => void;
}) {
  return (
    <section aria-label="Face similarity results">
      <p role="status">{resultText[page.state]}</p>
      {page.reasons.length > 0 && <p>{page.reasons.join(", ")}</p>}
      <p className="help">
        {page.compatible_count} compatible of {page.reference_count} approved
        references · {page.scope} studio scope
      </p>
      <ul>
        {page.items.map((c) => (
          <li key={c.version.persona_id}>
            <strong>{c.version.content.name}</strong> · version{" "}
            {c.version.revision} · face cosine {c.face_cosine.toFixed(4)} ·
            image cosine {c.whole_cosine.toFixed(4)}
            <button className="secondary" onClick={() => select(c)}>
              Compare {c.version.content.name}
            </button>
          </li>
        ))}
      </ul>
      {page.has_more && (
        <p>
          Showing the first five candidates. More candidates meet the threshold.
        </p>
      )}
      <SearchEvidence page={page} />
    </section>
  );
}

function SearchEvidence({ page }: { page: SimilarityPage }) {
  return (
    <details>
      <summary>Search method and evidence</summary>
      <dl className="saved-fields">
        <div>
          <dt>Method</dt>
          <dd>{page.method}</dd>
        </div>
        <div>
          <dt>Calibration policy</dt>
          <dd>{page.policy_id}</dd>
        </div>
        <div>
          <dt>Reviewed evidence digest</dt>
          <dd>{page.evidence_sha256}</dd>
        </div>
        <div>
          <dt>Representation</dt>
          <dd>
            {page.representation
              ? `${page.representation.model} / ${page.representation.provider_revision} / ${page.representation.dimensions} dimensions`
              : "Quality blocked before representation"}
          </dd>
        </div>
      </dl>
      <p className="help">
        Face cosine ranks the best compatible reference per persona. Whole-image
        cosine is context only. These values are not identity probabilities or
        production clearance.
      </p>
    </details>
  );
}
