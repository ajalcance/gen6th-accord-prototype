import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";

export default function EvidenceReview(props: StudioState) {
  return (
    <section className="panel evidence-review">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">HUMAN REVIEW / FIXTURE ROLE</p>
          <h2>Review evidence</h2>
        </div>
        <Icon name="shield" size={25} />
      </div>
      <ReviewActor {...props} />
      <EvidenceItems {...props} />
      <label>
        Comment anchored to evidence gap
        <textarea
          maxLength={500}
          value={props.comment}
          onChange={(event) => props.setComment(event.target.value)}
          placeholder="Record what a reviewer would need…"
        />
      </label>
      <p className="help">
        An empty note records a declared demo-review statement. Editing the note
        clears prior decisions.
      </p>
      <button
        className="text-button full-width"
        onClick={() => props.ask("change")}
      >
        <Icon name="spark" />
        Help draft a change request
      </button>
      <ReviewDecision {...props} />
      <p className="help">
        This click is a browser interaction, not an authenticated approval. No
        ownership or real identity is verified.
      </p>
    </section>
  );
}
function ReviewActor(props: StudioState) {
  return (
    <div className="actor-context">
      <label>
        Demo review actor
        <select
          value={props.reviewActor}
          onChange={(event) =>
            props.dispatch({
              type: "reviewActor",
              actor: event.target.value === "creator" ? "creator" : "reviewer",
            })
          }
        >
          <option value="reviewer">
            Mira Chen · independent fictional reviewer
          </option>
          <option value="creator">North Studio · fictional creator</option>
        </select>
      </label>
      {props.reviewActor === "creator" ? (
        <p role="status" className="warning-text">
          A creator cannot review their own version. Select the independent
          fictional reviewer.
        </p>
      ) : (
        <p className="help">
          Scenario role only. Real roles must come from trusted sessions.
        </p>
      )}
    </div>
  );
}
function EvidenceItems(props: StudioState) {
  return (
    <ol className="evidence-checklist">
      <li>
        <span className="evidence-symbol">
          <Icon name="file" />
        </span>
        <div>
          <strong>Concept & direction</strong>
          <p>
            {props.draft.contribution || "Human contribution not supplied."}
          </p>
          <small>Creator assertion · fixture-v{props.revision}</small>
        </div>
      </li>
      <li>
        <span className="evidence-symbol">
          <Icon name="file" />
        </span>
        <div>
          <strong>Canonical illustration</strong>
          <p>Original SVG study supplied with this preview.</p>
          <button
            className="text-button"
            disabled={props.analysis !== "ready"}
            onClick={() => props.setCandidate(true)}
          >
            Inspect illustration evidence
            <Icon name="arrow" />
          </button>
          {props.analysis !== "ready" && (
            <small>Load the demo scenario to inspect the comparison.</small>
          )}
        </div>
      </li>
      <EvidenceGap {...props} />
    </ol>
  );
}
function ReviewDecision(props: StudioState) {
  return (
    <div className="decision-area">
      <ReviewBlockers {...props} />
      <div className="button-row review-actions">
        <button
          className="secondary"
          onClick={() => {
            props.invalidate();
            props.setStep(1);
          }}
        >
          Request changes
        </button>
        <button
          className="primary"
          disabled={
            props.analysis !== "ready" ||
            !props.canReview ||
            props.dirty ||
            props.reviewActor !== "reviewer"
          }
          onClick={() => {
            if (props.recordReview()) props.setStep(3);
          }}
        >
          Record demo review
          <Icon name="arrow" />
        </button>
      </div>
    </div>
  );
}

function EvidenceGap(props: StudioState) {
  return (
    <li>
      <span className="evidence-symbol warning">!</span>
      <div>
        <strong>Evidence gap</strong>
        <p>
          No generation log or reference permissions are supplied. Real review
          remains pending.
        </p>
        <button className="text-button" onClick={() => props.ask("evidence")}>
          Explain what is missing
          <Icon name="arrow" />
        </button>
      </div>
    </li>
  );
}

function ReviewBlockers(props: StudioState) {
  const blockers = [
    !props.canReview && "Complete all four System Capture fields.",
    props.dirty && "Save the edited version before reviewing.",
    props.analysis !== "ready" &&
      "Run the demo scenario to inspect references.",
    props.reviewActor !== "reviewer" && "Choose the independent demo reviewer.",
  ].filter(Boolean);
  return (
    <>
      {blockers.length > 0 && (
        <div className="decision-blockers">
          <strong>Before recording a review</strong>
          <ul>
            {blockers.map((reason) => (
              <li key={String(reason)}>{reason}</li>
            ))}
          </ul>
          {(!props.canReview || props.dirty) && (
            <button className="text-button" onClick={() => props.setStep(1)}>
              Open System Capture record <Icon name="arrow" />
            </button>
          )}
        </div>
      )}
    </>
  );
}
