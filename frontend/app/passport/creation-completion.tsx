import { useEffect, useRef, useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import { CreationFields, CreationReceipt } from "./record-creation-fields";

type CompletionProps = {
  version: PersonaVersion | null;
  fields: Record<string, string>;
  records: () => void;
  open?: (id: string) => void;
  prepare?: (id: string) => void;
  restart: () => void;
};
export default function CreationCompletion({
  version,
  fields,
  records,
  open,
  prepare,
  restart,
}: CompletionProps) {
  const heading = useRef<HTMLHeadingElement>(null);
  const [showDraft, setShowDraft] = useState(false);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  return (
    <section
      className="record-creation creation-completion"
      aria-label="System Capture complete"
    >
      <h1 ref={heading} tabIndex={-1}>
        {version ? "System Capture saved" : "System Capture already saved"}
      </h1>
      <p className="help">
        {version
          ? "Your record and first approved portrait are saved. Continue with face processing, or open the performer workspace."
          : "This System Capture was confirmed earlier. Find it in Records before starting another capture."}
      </p>
      {version && <CreationReceipt version={version} fields={fields} />}
      <CompletionActions
        {...{ version, fields, records, open, prepare, restart }}
      />
      <button
        className="text-button"
        aria-expanded={showDraft}
        onClick={() => setShowDraft(!showDraft)}
      >
        {showDraft ? "Hide retained draft" : "View retained draft"}
      </button>
      {showDraft && (
        <fieldset disabled aria-label="Retained System Capture draft">
          <legend>Retained draft</legend>
          <CreationFields fields={fields} change={() => {}} />
        </fieldset>
      )}
    </section>
  );
}
function CompletionActions({
  version,
  records,
  open,
  prepare,
  restart,
}: CompletionProps) {
  return (
    <div className="creation-actions">
      {version && prepare && (
        <button className="primary" onClick={() => prepare(version.persona_id)}>
          Prepare recognition
        </button>
      )}
      {version && open && (
        <button className="secondary" onClick={() => open(version.persona_id)}>
          Open saved record
        </button>
      )}
      <button className="secondary" onClick={records}>
        Back to records
      </button>
      <button className="secondary" onClick={restart}>
        Start another System Capture
      </button>
    </div>
  );
}
