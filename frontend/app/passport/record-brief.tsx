import type { PersonaVersion } from "../../lib/persona-contracts";
import type { ReviewerBrief } from "../../lib/persona-assistant";
import { useGovernanceAccess } from "./saved-governance-read";
import type { SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";

const FAILURE: Record<string, string> = {
  unavailable:
    "A brief could not be drafted right now. The saved record is unchanged. Try again in a moment.",
};

function BriefList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <>
      <h4>{title}</h4>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </>
  );
}
function BriefResult({ brief }: { brief: ReviewerBrief }) {
  return (
    <div className="governance-card" data-state={brief.state}>
      <p className="eyebrow">
        {brief.state === "brief"
          ? "AI DRAFT · NOT A DECISION"
          : "NOT ENOUGH TEXT TO SUMMARISE"}
      </p>
      <p>{brief.summary}</p>
      <BriefList title="Facts a reviewer may still need" items={brief.gaps} />
      <BriefList
        title="Questions to ask the creator"
        items={brief.questions}
      />
      <p className="governance-notice">{brief.notice}</p>
      <p className="help">
        Drafted by {brief.model} ({brief.model_revision}) at{" "}
        {new Date(brief.generated_at).toLocaleString()}. Not saved; generating
        again may give different wording.
      </p>
    </div>
  );
}
/** Explicit, per-click request. Nothing is sent to the model until the user presses the button. */
export default function RecordBrief({
  source,
  version,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
}) {
  const gateway = source.assistant;
  const { query, state } = usePersonaQuery<ReviewerBrief>();
  useGovernanceAccess(state.phase);
  if (!gateway || gateway.workspaceId !== source.workspaceId) return null;
  const loading = state.phase === "loading";
  const brief =
    state.phase === "ready" &&
    state.value.version_id === version.version_id &&
    state.value.revision === version.revision
      ? state.value
      : null;
  return (
    <section className="record-brief" aria-label="Reviewer brief">
      <h3>Reviewer brief</h3>
      <p className="help">
        Optional. Press the button to send this version&apos;s name, biography,
        human contribution and AI disclosure to Google Gemini on Vertex AI for
        a short summary. The result is advice for a human reviewer, not a
        decision.
      </p>
      <button
        className="secondary"
        disabled={loading}
        onClick={() =>
          void query.run((signal) =>
            gateway.brief(version.persona_id, version.revision, signal),
          )
        }
      >
        {loading
          ? "Drafting…"
          : brief
            ? "Draft again"
            : "Draft reviewer brief"}
      </button>
      <div aria-live="polite">
        {loading && <p role="status">Drafting a brief with Gemini…</p>}
        {brief && <BriefResult brief={brief} />}
        {state.phase !== "ready" &&
          state.phase !== "idle" &&
          state.phase !== "loading" && (
            <p role="alert">
              {FAILURE[state.phase] ?? state.message}
            </p>
          )}
      </div>
    </section>
  );
}
