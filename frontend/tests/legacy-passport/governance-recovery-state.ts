import { useEffect, useMemo, useRef, useState } from "react";
import type { PersonaVersion, SaveCommand } from "../../lib/persona-contracts";
import {
  PersonaMutation,
  type MutationState,
} from "../../lib/persona-mutation";
import type { Draft } from "./fixture-data";
import { EXAMPLE_PERSONA } from "./governance-fixtures";
import {
  saveRecoveryPreview,
  type RecoveryScenario,
} from "./governance-save-preview";

export function useRecoveryExample(scenario: RecoveryScenario) {
  const mutation = useMemo(() => {
    const gateway = saveRecoveryPreview(scenario);
    return new PersonaMutation<SaveCommand, PersonaVersion>((command, signal) =>
      gateway.save(command, signal),
    );
  }, [scenario]);
  const alive = useRef(true);
  const [state, setState] = useState<MutationState<PersonaVersion>>({
    phase: "idle",
  });
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      mutation.cancel();
    };
  }, [mutation]);
  async function run(promise: Promise<MutationState<PersonaVersion>>) {
    setState(mutation.snapshot);
    const result = await promise;
    if (alive.current) setState(result);
  }
  return {
    state,
    intent: mutation.intent,
    submit: (draft: Draft) => run(mutation.submit(exampleSave(draft))),
    retry: () => run(mutation.retry()),
    cancel: () => mutation.cancel(),
  };
}

function exampleSave(draft: Draft): SaveCommand {
  return {
    request_id: crypto.randomUUID(),
    persona_id: EXAMPLE_PERSONA,
    expected_revision: 2,
    content: {
      name: draft.name,
      biography: draft.bio,
      human_contribution: draft.contribution,
      ai_disclosure: draft.disclosure,
    },
  };
}
