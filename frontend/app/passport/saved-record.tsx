import { useCallback, useEffect, useRef, useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { QueryState } from "../../lib/persona-query";
import type { SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";
import { GovernanceAccessLoss } from "./saved-governance-read";
import type {
  JourneyPage,
  RecordNavigation,
  RecordSection,
} from "./workspace-pages";
import RecordContent from "./record-content";
import RecordBrief from "./record-brief";
import RecordJourney from "./record-journey";
import RecordVersionPicker from "./record-version-picker";

export function ReadFeedback<T>({
  state,
  retry,
  cancel,
  resource,
}: {
  state: QueryState<T>;
  retry: () => void;
  cancel: () => void;
  resource?: string;
}) {
  if (state.phase === "ready" || state.phase === "idle") return null;
  return (
    <div
      className="saved-feedback read-feedback"
      data-phase={state.phase}
      role={state.phase === "loading" ? "status" : "alert"}
    >
      <p>
        {state.phase === "loading"
          ? `Loading ${resource?.toLowerCase() ?? "saved records"}…`
          : state.phase === "unavailable" && resource
            ? `Could not load ${resource.toLowerCase()}. Try again or check capability status in Settings.`
            : state.message}
      </p>
      {state.phase === "loading" && (
        <button className="secondary" onClick={cancel}>
          Stop loading
        </button>
      )}
      {["unavailable", "cancelled"].includes(state.phase) && (
        <button className="secondary" onClick={retry}>
          Try again
        </button>
      )}
    </div>
  );
}

type Props = {
  source: SavedPersonaSource;
  personaId: string;
  revision?: number | null;
  journey?: JourneyPage;
  initialSection?: RecordSection;
  navigation?: RecordNavigation;
  close: () => void;
};
function useSavedVersion(props: Props) {
  const { source, personaId, navigation } = props;
  const { query, state } = usePersonaQuery<PersonaVersion>();
  const [accessLost, setAccessLost] = useState(false);
  const [localRevision, setLocalRevision] = useState<number | null>(null);
  const revision = navigation ? (props.revision ?? null) : localRevision;
  const denied = useCallback(() => {
    query.clear();
    setAccessLost(true);
  }, [query]);
  useEffect(() => {
    if (source.gateway.workspaceId !== source.workspaceId) return;
    void query.run((signal) =>
      source.gateway.load(personaId, revision, signal),
    );
    return () => query.stop();
  }, [query, source.gateway, source.workspaceId, personaId, revision]);
  const version =
    state.phase === "ready" &&
    !accessLost &&
    source.gateway.workspaceId === source.workspaceId &&
    state.value.persona_id === personaId &&
    (revision === null || state.value.revision === revision)
      ? state.value
      : null;
  const loaded = navigation?.loaded;
  useEffect(() => {
    if (version) loaded?.(version.persona_id, version.revision);
  }, [loaded, version]);
  function choose(value: number | null) {
    if (value === revision) {
      void query.retry();
      return;
    }
    query.clear();
    if (navigation) navigation.version(value);
    else setLocalRevision(value);
  }
  return { query, state, accessLost, revision, denied, version, choose };
}
export default function SavedRecord(props: Props) {
  const current = useSavedVersion(props);
  const { query, state, accessLost, version } = current;
  return (
    <section
      className="saved-record record-workspace"
      aria-label="Saved version"
      aria-busy={state.phase === "loading"}
    >
      <RecordHeading {...props} version={version} />
      {props.source.gateway.workspaceId !== props.source.workspaceId && (
        <p role="alert">The workspace connection could not be validated.</p>
      )}
      <ReadFeedback
        state={state}
        resource="Saved performer"
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {accessLost && (
        <p role="alert">
          Your session or permission for these governance records is no longer
          available. The saved view was cleared. Restore access and reopen saved
          records; your browser draft is unchanged.
        </p>
      )}
      {version && (
        <GovernanceAccessLoss.Provider value={current.denied}>
          <VersionWorkspace {...props} version={version} current={current} />
        </GovernanceAccessLoss.Provider>
      )}
    </section>
  );
}
function RecordHeading({
  journey,
  version,
  close,
}: Props & { version: PersonaVersion | null }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  return (
    <div className="panel-heading record-page-heading">
      <div>
        {!journey && <p className="eyebrow">SAVED PERFORMER</p>}
        <h1 ref={heading} tabIndex={-1}>
          {journey ?? version?.content.name ?? "Record"}
        </h1>
      </div>
      <button className="secondary" onClick={close}>
        {journey ? "Change performer" : "Back to saved records"}
      </button>
    </div>
  );
}
function VersionWorkspace(
  props: Props & {
    version: PersonaVersion;
    current: ReturnType<typeof useSavedVersion>;
  },
) {
  const { source, version, navigation, current } = props;
  const content = { source, version, navigation, denied: current.denied };
  return (
    <>
      <div className="record-context">
        <span>{version.content.name}</span>
        <RecordVersionPicker
          source={source}
          version={version}
          choose={current.choose}
        />
        <span className="help">
          {current.revision === null
            ? "Current version at last read"
            : "Selected saved version"}
        </span>
      </div>
      <RecordBrief key={version.version_id} source={source} version={version} />
      <div key={version.version_id}>
        {props.journey ? (
          <RecordJourney {...content} page={props.journey} />
        ) : (
          <RecordContent {...content} initialSection={props.initialSection} />
        )}
      </div>
    </>
  );
}
