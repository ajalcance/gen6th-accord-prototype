import type { ChangeEvent } from "react";
import type { PersonaDraft, PersonaVersion } from "../../lib/persona-contracts";

const fields: {
  key: keyof PersonaDraft;
  label: string;
  hint: string;
  max: number;
}[] = [
  {
    key: "name",
    label: "Persona name",
    hint: "Name this persona record.",
    max: 80,
  },
  {
    key: "biography",
    label: "Biography",
    hint: "Describe the persona and its intended context.",
    max: 500,
  },
  {
    key: "human_contribution",
    label: "Human contribution",
    hint: "Describe the human work, such as writing, direction or illustration.",
    max: 500,
  },
  {
    key: "ai_disclosure",
    label: "AI disclosure",
    hint: "Describe any AI use, or state that none was used.",
    max: 500,
  },
];

export function CreationFields({
  fields: values,
  change,
}: {
  fields: Record<string, string>;
  change: (field: string, value: string) => void;
}) {
  return (
    <div className="record-creation-fields">
      {fields.map((field) => (
        <CreationField
          key={field.key}
          field={field}
          value={values[field.key] ?? ""}
          change={change}
        />
      ))}
    </div>
  );
}
function CreationField({
  field,
  value,
  change,
}: {
  field: (typeof fields)[number];
  value: string;
  change: (field: string, value: string) => void;
}) {
  const count = [...value.trim()].length,
    id = `creation-${field.key}`;
  const input = creationInput(field, value, id, count, change);
  return (
    <details
      className="capture-field"
      open={field.key === "name" || count > field.max}
    >
      <summary>
        <span id={`${id}-label`}>{field.label}</span>
        <span className="capture-field-status">
          {count > field.max
            ? "Needs attention"
            : count
              ? "Entered"
              : "Required · incomplete"}
          <small id={`${id}-count`}>
            {count} / {field.max}
          </small>
        </span>
      </summary>
      <div
        className={`capture-field-input ${field.key === "name" ? "creation-name" : ""}`}
      >
        {field.key === "name" ? (
          <input {...input} />
        ) : (
          <textarea {...input} rows={3} />
        )}
        {count > field.max && (
          <span className="help" role="alert" id={`${id}-hint`}>
            Use at most {field.max} characters.
          </span>
        )}
      </div>
    </details>
  );
}

function creationInput(
  field: (typeof fields)[number],
  value: string,
  id: string,
  count: number,
  change: (field: string, value: string) => void,
) {
  return {
    id,
    required: true,
    "aria-labelledby": `${id}-label`,
    placeholder: field.hint,
    maxLength: field.max * 2,
    value,
    "aria-describedby": `${id}-count${count > field.max ? ` ${id}-hint` : ""}`,
    "aria-invalid": count > field.max,
    onInvalid: (
      event: React.InvalidEvent<HTMLInputElement | HTMLTextAreaElement>,
    ) => {
      const section = event.currentTarget.closest("details");
      if (section) section.open = true;
    },
    onChange: (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      change(field.key, event.target.value),
  };
}

export function CreationReceipt({
  version,
  fields: current,
}: {
  version: PersonaVersion;
  fields: Record<string, string>;
}) {
  const edited = fields.some(
    (field) => (current[field.key] ?? "").trim() !== version.content[field.key],
  );
  return (
    <section
      className="creation-receipt"
      aria-label="Saved System Capture receipt"
    >
      <h2>{version.content.name}</h2>
      <p>
        Saved version {version.revision} ·{" "}
        {new Date(version.recorded_at).toLocaleString()}
      </p>
      <details className="saved-receipt">
        <summary>Inspect storage receipt</summary>
        <dl>
          <dt>Record ID</dt>
          <dd>{version.persona_id}</dd>
          <dt>Version ID</dt>
          <dd>{version.version_id}</dd>
        </dl>
      </details>
      {edited && (
        <p className="help">
          Your fields include later edits. The receipt confirms the submitted
          version only; those edits have not been saved.
        </p>
      )}
      <p className="help">
        Independent review and evidence remain separate next steps.
      </p>
    </section>
  );
}
