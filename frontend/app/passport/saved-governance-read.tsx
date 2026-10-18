import { createContext, useContext, useEffect } from "react";
import { usePersonaQuery } from "./use-persona-query";

/** Permission loss in any panel removes the complete selected-record surface. */
export const GovernanceAccessLoss = createContext<() => void>(() => {});
export function useGovernanceAccess(phase: string) {
  const accessLost = useContext(GovernanceAccessLoss);
  useEffect(() => {
    if (phase === "denied") accessLost();
  }, [phase, accessLost]);
}
export function useGovernanceRead<T>(
  load: (signal: AbortSignal) => Promise<T>,
) {
  const read = usePersonaQuery<T>();
  const { query, state } = read;
  useGovernanceAccess(state.phase);
  useEffect(() => {
    void query.run(load);
    return () => query.clear();
  }, [query, load]);
  return read;
}

export function DiscoveryPager({
  cursor,
  next,
  ready,
  change,
  noun,
}: {
  cursor: string | number | null;
  next: string | number | null;
  ready: boolean;
  change: (value: string | number | null) => void;
  noun: string;
}) {
  if (cursor === null && next === null) return null;
  return (
    <div className="governance-pagination">
      <button
        className="secondary"
        disabled={!ready || cursor === null}
        onClick={() => change(null)}
      >
        First {noun}
      </button>
      <button
        className="secondary"
        disabled={!ready || next === null}
        onClick={() => change(next)}
      >
        More {noun}
      </button>
    </div>
  );
}
