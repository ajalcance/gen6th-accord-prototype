import { useEffect } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";
import { ReadFeedback } from "./saved-record";
import { ContentFields, VersionSnapshot } from "./version-snapshot";

type Props = {
  source: SavedPersonaSource;
  personaId: string;
  fields: Record<string, string>;
  blocked: boolean;
  use: (version: PersonaVersion) => void;
  denied: () => void;
};
export default function VersionReconciliation({
  source,
  personaId,
  fields,
  blocked,
  use,
  denied,
}: Props) {
  const { state, query } = usePersonaQuery<PersonaVersion>();
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  return (
    <section aria-label="Version reconciliation">
      <button
        type="button"
        className="secondary"
        disabled={state.phase === "loading" || blocked}
        onClick={() =>
          void query.run((signal) =>
            source.gateway.load(personaId, null, signal),
          )
        }
      >
        Compare latest saved version
      </button>
      <ReadFeedback
        state={state}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {state.phase === "ready" && (
        <>
          <DraftComparison fields={fields} latest={state.value} />
          <button
            className="secondary"
            disabled={blocked}
            onClick={() => {
              use(state.value);
              query.clear();
            }}
          >
            Use this version for a new intent
          </button>
        </>
      )}
    </section>
  );
}
function DraftComparison({
  fields,
  latest,
}: {
  fields: Record<string, string>;
  latest: PersonaVersion;
}) {
  return (
    <div className="governance-columns">
      <section>
        <h4>Your draft</h4>
        <ContentFields
          content={{
            name: fields.name ?? "",
            biography: fields.biography ?? "",
            human_contribution: fields.human_contribution ?? "",
            ai_disclosure: fields.ai_disclosure ?? "",
          }}
        />
      </section>
      <section>
        <h4>Latest saved version</h4>
        <VersionSnapshot version={latest} />
      </section>
    </div>
  );
}
