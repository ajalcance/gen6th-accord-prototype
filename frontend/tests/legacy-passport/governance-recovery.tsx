import { useState } from "react";
import type { PersonaVersion, SaveCommand } from "../../lib/persona-contracts";
import type { MutationState } from "../../lib/persona-mutation";
import { isDraftReady, type Draft } from "./fixture-data";
import { governancePreview } from "./governance-preview-transport";
import { EXAMPLE_PERSONA } from "./governance-fixtures";
import { GovernanceRead } from "../../app/passport/governance-common";
import { ContentFields, VersionSnapshot } from "./governance-versions";
import { usePersonaQuery } from "../../app/passport/use-persona-query";
import { useRecoveryExample } from "./governance-recovery-state";
import type { RecoveryScenario } from "./governance-save-preview";

export default function GovernanceRecovery({
  draft,
  close,
  connection,
}: {
  draft: Draft;
  close: () => void;
  connection: () => void;
}) {
  const [scenario, setScenario] = useState<RecoveryScenario>("conflict");
  return (
    <section className="governance-section" aria-label="Save recovery">
      <h3>Keep the draft. Resolve the outcome.</h3>
      <p>
        These examples use a snapshot of your browser draft. They never save,
        replace or publish it.
      </p>
      <label className="governance-select">
        Recovery example
        <select
          value={scenario}
          onChange={(event) =>
            setScenario(event.target.value as RecoveryScenario)
          }
        >
          <option value="conflict">Version conflict</option>
          <option value="unavailable">Unavailable service</option>
          <option value="denied">Permission lost</option>
        </select>
      </label>
      <RecoveryCase
        key={scenario}
        scenario={scenario}
        draft={draft}
        close={close}
        connection={connection}
      />
    </section>
  );
}

function RecoveryCase({
  scenario,
  draft,
  close,
  connection,
}: {
  scenario: RecoveryScenario;
  draft: Draft;
  close: () => void;
  connection: () => void;
}) {
  const recovery = useRecoveryExample(scenario);
  const phase = recovery.state.phase;
  return (
    <div className="governance-card">
      {phase === "idle" && (
        <LaunchExample
          draft={draft}
          submit={() => void recovery.submit(draft)}
        />
      )}
      {phase === "pending" && (
        <div role="status">
          <p>Waiting for the fictional response…</p>
          <button className="secondary" onClick={recovery.cancel}>
            Stop waiting
          </button>
        </div>
      )}
      {phase !== "idle" && phase !== "pending" && (
        <RecoveryResult
          state={recovery.state}
          intent={recovery.intent}
          retry={() => void recovery.retry()}
          connection={connection}
        />
      )}
      {phase === "conflict" && recovery.intent && (
        <ConflictComparison intent={recovery.intent} />
      )}
      <button className="text-button" onClick={close}>
        Keep draft & close
      </button>
    </div>
  );
}

function RecoveryResult({
  state,
  intent,
  retry,
  connection,
}: {
  state: MutationState<PersonaVersion>;
  intent: SaveCommand | null;
  retry: () => void;
  connection: () => void;
}) {
  if (state.phase === "idle" || state.phase === "pending") return null;
  return (
    <div role={state.phase === "succeeded" ? "status" : "alert"}>
      {state.phase === "succeeded" ? (
        <>
          <h3>Example retry resolved</h3>
          <p>
            No real save occurred. Your browser draft and its local version are
            unchanged.
          </p>
        </>
      ) : (
        <p>{"message" in state ? state.message : ""}</p>
      )}
      {(state.phase === "retryable" || state.phase === "cancelled") && (
        <button className="secondary" onClick={retry}>
          Retry same example request
        </button>
      )}
      {state.phase === "denied" && (
        <>
          <p className="help">
            No fallback login is available. A verified session and permission
            must be restored before a real save.
          </p>
          <button className="secondary" onClick={connection}>
            Connection details
          </button>
        </>
      )}
      {intent && <RequestSnapshot intent={intent} />}
    </div>
  );
}

function ConflictComparison({ intent }: { intent: SaveCommand }) {
  const { state, query } = usePersonaQuery<PersonaVersion>();
  return (
    <div className="governance-comparison">
      <button
        className="secondary"
        disabled={state.phase === "loading"}
        onClick={() =>
          void query.run((signal) =>
            governancePreview().load(EXAMPLE_PERSONA, null, signal),
          )
        }
      >
        Compare latest example version
      </button>
      <GovernanceRead state={state} query={query}>
        {(version) => (
          <>
            <p className="help">
              Separate fictional record · no merge or overwrite occurs. Review
              the differences before preparing a new save intent.
            </p>
            <div className="governance-columns">
              <section>
                <h3>Your preserved draft</h3>
                <ContentFields content={intent.content} />
              </section>
              <section>
                <h3>Latest fictional version</h3>
                <VersionSnapshot version={version} />
              </section>
            </div>
          </>
        )}
      </GovernanceRead>
    </div>
  );
}

function LaunchExample({
  draft,
  submit,
}: {
  draft: Draft;
  submit: () => void;
}) {
  return (
    <>
      <p className="help">
        No request has run. Your draft remains in the System Capture screen.
      </p>
      <button
        className="secondary"
        disabled={!isDraftReady(draft)}
        onClick={submit}
      >
        Run recovery example
      </button>
      {!isDraftReady(draft) && (
        <p className="help">
          Complete the four System Capture fields to preview recovery.
        </p>
      )}
    </>
  );
}

function RequestSnapshot({ intent }: { intent: SaveCommand }) {
  return (
    <details>
      <summary>Preserved request snapshot</summary>
      <dl className="governance-fields">
        <div>
          <dt>Request ID</dt>
          <dd>{intent.request_id}</dd>
        </div>
        <div>
          <dt>Expected version</dt>
          <dd>{intent.expected_revision}</dd>
        </div>
        <div>
          <dt>Draft name</dt>
          <dd>{intent.content.name}</dd>
        </div>
      </dl>
    </details>
  );
}
