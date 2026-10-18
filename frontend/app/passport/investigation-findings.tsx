import type { InvestigationResult } from "../../lib/persona-investigation-contracts";

const labels = {
  facial_features_similar: "Selected facial features appear similar",
  facial_features_different: "Selected facial features appear different",
  pose_differs: "Pose differs between the appearances",
  appearance_differs: "Appearance differs between the supplied images",
  comparison_uncertain: "Visual comparison remains uncertain",
};
const gaps = {
  identity_not_established:
    "Performer identity is not established by this comparison.",
  rights_not_verified:
    "Ownership, consent and production permission still need evidence and review.",
  source_context_unverified:
    "The supplied source context is an attributed statement, not verified web discovery.",
};
export default function InvestigationFindings({
  result,
}: {
  result: InvestigationResult;
}) {
  return (
    <section aria-label="Grounded investigation findings">
      <h4>Analysis #{result.ordinal} · human review required</h4>
      <p>
        {result.findings.state === "insufficient_evidence"
          ? "The model abstained: insufficient evidence for visual observations."
          : "Model observations from the two authorized images:"}
      </p>
      <ul>
        {result.findings.observations.map((row) => (
          <li key={row.label}>
            {labels[row.label]} · evidence: {row.citations.join(" + ")}
          </li>
        ))}
      </ul>
      <h4>Evidence gaps</h4>
      <ul>
        {result.gaps.map((gap) => (
          <li key={gap}>{gaps[gap]}</li>
        ))}
      </ul>
      <p>
        Supplied source context: {result.source_note} · recorded by{" "}
        {result.actor_ref}
      </p>
      <EvidenceReceipt result={result} />
    </section>
  );
}
function EvidenceReceipt({ result: r }: { result: InvestigationResult }) {
  const rows = [
    ["Analysis ID", r.id],
    ["Exact version", r.version_id],
    ["Recorded at", r.recorded_at],
    ["Model / observed revision", `${r.model} / ${r.provider_revision}`],
    ["Recipe", r.recipe],
    ["Supplied image SHA-256", r.query.source_sha256],
    ["Query analysis SHA-256", r.query.analysis_sha256],
    [
      "Approved reference / generation",
      `${r.portrait_id} / ${r.generation_id}`,
    ],
    ["Reference analysis SHA-256", r.reference_sha256],
    [
      "Selected faces",
      `query ${r.search.face_index + 1} / reference ${r.reference_face.index + 1}`,
    ],
    [
      "Fresh search receipt / scope",
      `${r.search.request_id} / ${r.search.scope}`,
    ],
    ["Search method / policy", `${r.search.method} / ${r.search.policy_id}`],
    ["Calibration evidence", r.search.evidence_sha256],
    [
      "Raw cosine values",
      `face ${r.search.face_cosine.toFixed(4)} / image ${r.search.whole_cosine.toFixed(4)}`,
    ],
  ];
  return (
    <details>
      <summary>Inspect source-bound evidence packet</summary>
      <dl className="saved-fields">
        {rows.map(([title, value]) => (
          <div key={title}>
            <dt>{title}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <p className="help">
        Encrypted findings and provenance are retained in this studio. Query
        pixels remain transient and expire at {r.query.expires_at}. Scores are
        not identity probabilities. Saved findings do not grant production
        permission.
      </p>
    </details>
  );
}
