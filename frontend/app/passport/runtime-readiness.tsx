import { useCallback } from "react";
import type {
  RuntimeGateway,
  RuntimeReadiness,
} from "../../lib/persona-runtime";
import { GovernanceRead } from "./governance-common";
import { useGovernanceRead } from "./saved-governance-read";

export function useRuntimeReadiness(gateway: RuntimeGateway) {
  const load = useCallback(
    (signal: AbortSignal) => gateway.readiness(signal),
    [gateway],
  );
  return { ...useGovernanceRead(load), load };
}
export default function RuntimeReadinessPanel({
  gateway,
}: {
  gateway: RuntimeGateway;
}) {
  const { state, query, load } = useRuntimeReadiness(gateway);
  return (
    <section
      className="runtime-readiness"
      aria-label="Processing connection configuration"
    >
      <h3>Processing &amp; passport configuration</h3>
      <GovernanceRead
        state={state}
        query={query}
        resource="Processing configuration"
      >
        {(ready) => <RuntimeFlags ready={ready} />}
      </GovernanceRead>
      <button
        className="secondary"
        disabled={state.phase === "loading"}
        onClick={() => void query.run(load)}
      >
        Refresh processing configuration
      </button>
      <p className="help">
        Configuration does not certify live provider availability or retrieval
        accuracy. Measured acceptance remains separate.
      </p>
    </section>
  );
}
function RuntimeFlags({ ready }: { ready: RuntimeReadiness }) {
  const flags: [string, boolean][] = [
    ["Durable face processing", ready.face_jobs_configured],
    ["Calibrated private search", ready.search_configured],
    ["Grounded comparison", ready.investigation_configured],
    ["Passport signing", ready.signing_configured],
    ["Trusted verification", ready.verification_configured],
  ];
  return (
    <dl>
      {flags.map(([label, configured]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{configured ? "Configured" : "Unavailable"}</dd>
        </div>
      ))}
    </dl>
  );
}
