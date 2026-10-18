import { useCallback } from "react";
import type {
  PersonaVersion,
  ReviewCommand,
} from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { useGovernanceRead } from "./saved-governance-read";
import { GovernanceRead } from "./governance-common";
import { usePreparedWrite, useWriteDraft } from "./prepared-write-state";
import {
  writeKey,
  WriteFeedback,
  ReloadWrite,
  SubmitWriteForm,
  DecisionFields,
} from "./prepared-write-common";

type Props = {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
};
function useReviewWrite({ source, version, denied }: Props) {
  const key = writeKey(source, "review", version.version_id);
  const draft = useWriteDraft(key, {
    decision: "changes_requested",
    statement: "",
    confirm: "",
  });
  const mutation = usePreparedWrite(
    source.writeGateway!,
    "review",
    key,
    denied,
  );
  const load = useCallback(
    (signal: AbortSignal) =>
      source.gateway.reads.reviewHistory(
        version.version_id,
        { before_ordinal: null, limit: 1 },
        signal,
      ),
    [source.gateway, version.version_id],
  );
  const read = useGovernanceRead(load);
  const submit = (previous: string | null) =>
    void mutation.submit({
      request_id: crypto.randomUUID(),
      version_id: version.version_id,
      expected_previous_id: previous,
      decision: draft.fields.decision as ReviewCommand["decision"],
      statement: draft.fields.statement,
    });
  return { draft, mutation, ...read, load, submit };
}

export default function PreparedReviewWrite(props: Props) {
  const action = useReviewWrite(props),
    { draft, mutation, state, query, load } = action;
  return (
    <section aria-label="Record an independent review">
      <h3>Review decision</h3>
      <p className="help">
        Only a currently authorized independent human reviewer can record this
        decision. Approval does not establish legal rights.
      </p>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <>
            <p className="help">
              {page.items.length
                ? "Latest decision: " + page.items[0].decision
                : "No previous decision for this version."}
            </p>
            <SubmitWriteForm
              draft={draft}
              mutation={mutation}
              ready={!!draft.fields.statement?.trim()}
              label="Record review"
              confirmation="I reviewed this exact version and evidence before making this decision."
              submit={() => action.submit(page.items[0]?.id ?? null)}
            >
              <DecisionFields draft={draft} />
            </SubmitWriteForm>
          </>
        )}
      </GovernanceRead>
      <WriteFeedback {...mutation} retry={() => void mutation.retry()} />
      <ReloadWrite
        draft={draft}
        mutation={mutation}
        loading={state.phase === "loading"}
        reload={() => void query.run(load)}
        label="Reload review before a new intent"
      />
    </section>
  );
}
