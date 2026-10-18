import Portrait from "./portrait";
import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";
import type { Draft } from "./fixture-data";

const FIELDS: { key: keyof Draft; label: string; hint: string; max: number }[] =
  [
    {
      key: "name",
      label: "Persona name",
      hint: "A name for the character, not a verified personal identity.",
      max: 80,
    },
    {
      key: "bio",
      label: "Biography",
      hint: "Describe the fictional persona and its creative context.",
      max: 500,
    },
    {
      key: "contribution",
      label: "Human contribution",
      hint: "Name the human work: concept, direction, writing or illustration.",
      max: 500,
    },
    {
      key: "disclosure",
      label: "AI disclosure",
      hint: "Describe synthetic elements and missing generation evidence.",
      max: 500,
    },
  ];
export default function Creation(props: StudioState) {
  return (
    <div className="creation-layout">
      <CreationForm {...props} />
      <div className="creation-aside">
        <DraftPreview {...props} />
        <EvidenceInventory {...props} />
      </div>
    </div>
  );
}
function CreationForm(props: StudioState) {
  const completed = FIELDS.filter((field) =>
    (props.draft[field.key] ?? "").trim(),
  ).length;
  return (
    <form
      className="panel creation-form"
      aria-label="System Capture"
      onSubmit={(event) => {
        event.preventDefault();
        if (props.canReview) {
          props.dispatch({ type: "commit" });
          props.setStep(2);
        }
      }}
    >
      <div className="panel-heading">
        <div>
          <p className="eyebrow">01 / SYSTEM CAPTURE RECORD</p>
          <h2>Character details</h2>
        </div>
        <span className="status">{completed} / 4 complete</span>
      </div>
      <p className="help">
        Use fictional content only. This draft is stored in this browser; it is
        not a backend record.
      </p>
      <div className="form-section-title">
        <span>01</span>
        <h3>Character & contribution</h3>
      </div>
      <div className="creation-fields">
        {FIELDS.map((field) => (
          <CreationField key={field.key} field={field} {...props} />
        ))}
      </div>
      <div className="form-actions">
        <div role="status" className="help">
          {props.storage}
          {!props.canReview &&
            " · Complete the name, biography and contribution to continue. AI disclosure is also required."}
        </div>
        <button className="primary" type="submit" disabled={!props.canReview}>
          Save version & open analysis
          <Icon name="arrow" />
        </button>
      </div>
    </form>
  );
}
function CreationField(
  props: StudioState & { field: (typeof FIELDS)[number] },
) {
  const { field, draft, update } = props;
  const value = draft[field.key] ?? "";
  return (
    <label className="draft-field">
      <span className="field-heading">
        {field.label}
        <small>
          {value !== props.committed[field.key] && "Edited · "}
          {value.length} / {field.max}
        </small>
      </span>
      {field.key === "name" ? (
        <input
          aria-label={field.label}
          aria-describedby={`hint-${field.key}`}
          required
          maxLength={field.max}
          value={value}
          onChange={(event) => update(field.key, event.target.value)}
        />
      ) : (
        <textarea
          aria-label={field.label}
          aria-describedby={`hint-${field.key}`}
          required
          maxLength={field.max}
          value={value}
          onChange={(event) => update(field.key, event.target.value)}
        />
      )}
      <span className="field-hint" id={`hint-${field.key}`}>
        {field.hint}
      </span>
    </label>
  );
}
function DraftPreview(props: StudioState) {
  return (
    <section className="preview-card creation-preview">
      <div className="preview-art">
        <Portrait variant={props.variant} />
        <span className="portrait-tag">LIVE DRAFT PREVIEW</span>
      </div>
      <div>
        <p className="eyebrow">DRAFT PREVIEW / FICTIONAL</p>
        <h2>{props.draft.name || "Your persona"}</h2>
        <p>
          {props.draft.bio || "The story begins with your fictional character."}
        </p>
        <span className="status">
          {props.dirty ? "Edited draft" : "Fixture draft"} · unsigned
        </span>
        <p className="help">
          {props.dirty
            ? `Changes are saved as a browser draft. Version ${props.revision} has not been replaced.`
            : `Matches committed fixture version ${props.revision}.`}
        </p>
      </div>
    </section>
  );
}
function EvidenceInventory(props: StudioState) {
  return (
    <section className="panel evidence-inventory">
      <div className="panel-heading">
        <h3>Evidence inventory</h3>
        <span className="status">1 supplied</span>
      </div>
      <details className="evidence-item evidence-details">
        <summary>
          Inspect supplied illustration <Icon name="file" />
        </summary>
        <Icon name="file" />
        <div>
          <strong>character-study.svg</strong>
          <p>Original vector fixture · palette {props.variant + 1}</p>
        </div>
        <Portrait variant={props.variant} />
        <p className="help">
          Supplied original SVG fixture. Presence is not a verified rights
          claim.
        </p>
      </details>
      <div className="evidence-gap">
        <span className="status warning">Evidence gap</span>
        <p>Generation logs and reference permissions are not supplied.</p>
        <ul className="evidence-gaps">
          <li>Generation record · missing</li>
          <li>Reference permissions · missing</li>
        </ul>
        <button className="text-button" onClick={() => props.ask("evidence")}>
          What should I provide?
          <Icon name="arrow" />
        </button>
      </div>
      <p className="availability-note">
        Uploads unavailable in this local demo
      </p>
      <p className="help">
        Real evidence needs quarantine, validation, scoped encryption and
        trusted sessions.
      </p>
    </section>
  );
}
