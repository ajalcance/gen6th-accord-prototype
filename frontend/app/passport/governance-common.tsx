import type { ReactNode } from "react";
import type { PersonaQuery, QueryState } from "../../lib/persona-query";
import { ReadFeedback } from "./saved-record";

export function GovernanceRead<T>({
  state,
  query,
  children,
  resource,
}: {
  state: QueryState<T>;
  query: PersonaQuery<T>;
  children: (value: T) => ReactNode;
  resource?: string;
}) {
  return (
    <>
      <ReadFeedback
        state={state}
        resource={resource}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {state.phase === "ready" && children(state.value)}
    </>
  );
}

export function GovernanceEmpty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="governance-empty" role="status">
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}

export function RecordedTime({ value }: { value: string }) {
  return (
    <time dateTime={value}>
      {value.replace("T", " · ").replace("Z", " UTC")}
    </time>
  );
}

export function Unsigned() {
  return <span className="status neutral">Unsigned</span>;
}

export function HistoryPager({
  cursor,
  state,
  setCursor,
  noun,
}: {
  cursor: number | null;
  state: QueryState<{ next_before_ordinal: number | null }>;
  setCursor: (value: number | null) => void;
  noun: string;
}) {
  const next = state.phase === "ready" ? state.value.next_before_ordinal : null;
  const blocked = state.phase !== "ready";
  if (cursor === null && next === null) return null;
  return (
    <div className="governance-pagination">
      <button
        className="secondary"
        disabled={blocked || cursor === null}
        onClick={() => setCursor(null)}
      >
        Newest {noun}
      </button>
      <button
        className="secondary"
        disabled={blocked || next === null}
        onClick={() => setCursor(next)}
      >
        Older {noun}
      </button>
    </div>
  );
}
