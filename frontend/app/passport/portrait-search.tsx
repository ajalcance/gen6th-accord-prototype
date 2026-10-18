import { useEffect, useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import { preparePhoto } from "../../lib/persona-photos";
import type { PortraitSearchPage } from "../../lib/persona-portrait-search";
import { requireContract } from "../../lib/persona-validation";
import type { SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";
import { ReadFeedback } from "./saved-record";
import SavedPhoto from "./saved-photo";
import { VersionSnapshot } from "./version-snapshot";

export default function PortraitSearch({
  source,
  expanded = false,
}: {
  source: SavedPersonaSource;
  expanded?: boolean;
}) {
  const search = usePortraitSearch(source);
  return (
    <details
      className={`panel portrait-search${expanded ? " search-expanded" : ""}`}
      open={expanded || undefined}
    >
      <summary>Search by portrait</summary>
      <p className="help">
        Find registered portraits with identical file bytes in this workspace.
        Use the face similarity panel for a prepared face query. This search
        does not register your query image.
      </p>
      <SearchControls search={search} />
      <ReadFeedback
        state={search.state}
        retry={() => void search.query.retry()}
        cancel={() => search.query.cancel()}
      />
      {search.accessLost && (
        <p role="alert">
          Workspace access is no longer available. Search results were cleared.
        </p>
      )}
      {search.state.phase === "ready" && (
        <SearchResults page={search.state.value} select={search.setSelected} />
      )}
      {search.selected && search.state.phase === "ready" && (
        <MatchedPortrait
          key={search.selected.version_id}
          source={source}
          candidate={search.selected}
          denied={search.loseAccess}
        />
      )}
    </details>
  );
}

function usePortraitSearch(source: SavedPersonaSource) {
  const { query, state } = usePersonaQuery<PortraitSearchPage>();
  const [file, setFile] = useState<File | null>(null);
  const [selected, setSelected] = useState<PersonaVersion | null>(null);
  const [accessLost, setAccessLost] = useState(false);
  const gateway = source.portraitSearch;
  const available = gateway?.workspaceId === source.workspaceId;
  const pending = state.phase === "loading";
  const fileError = localFileError(file);
  const search = () => {
    if (!file || !gateway || !available || fileError) return;
    setSelected(null);
    setAccessLost(false);
    void query.run(async (signal) => {
      const command = await preparePhoto(file);
      if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
      return gateway.search(command, signal);
    });
  };
  const clear = () => {
    query.clear();
    setFile(null);
    setSelected(null);
  };
  return {
    query,
    state,
    file,
    setFile,
    selected,
    setSelected,
    available,
    pending,
    fileError,
    search,
    clear,
    accessLost,
    loseAccess: () => {
      query.clear();
      setSelected(null);
      setAccessLost(true);
    },
  };
}

function localFileError(file: File | null): string {
  return file &&
    (!["image/png", "image/jpeg"].includes(file.type) ||
      file.size < 1 ||
      file.size > 10485760)
    ? "Choose a PNG or JPEG file between 1 byte and 10 MB."
    : "";
}

function SearchControls({
  search: flow,
}: {
  search: ReturnType<typeof usePortraitSearch>;
}) {
  return (
    <>
      <div className="photo-actions">
        <SearchPicker flow={flow} />
        <button
          className="secondary"
          disabled={
            !flow.available || !flow.file || flow.pending || !!flow.fileError
          }
          onClick={flow.search}
        >
          Find identical portraits
        </button>
        {flow.file && (
          <button className="secondary" onClick={flow.clear}>
            Clear image search
          </button>
        )}
      </div>
      <p className="help">
        PNG or JPEG · up to 10 MB{flow.file ? ` · ${flow.file.name}` : ""}
      </p>
      {flow.fileError && <p role="alert">{flow.fileError}</p>}
      {!flow.available && (
        <p role="status">
          Image search requires a connected workspace search service.
        </p>
      )}
    </>
  );
}

function SearchPicker({
  flow,
}: {
  flow: ReturnType<typeof usePortraitSearch>;
}) {
  return (
    <label className="photo-picker">
      Choose search image
      <input
        type="file"
        accept="image/png,image/jpeg"
        disabled={flow.pending || !flow.available}
        onChange={(event) => {
          flow.clear();
          flow.setFile(event.target.files?.[0] ?? null);
          event.target.value = "";
        }}
      />
    </label>
  );
}

function SearchResults({
  page,
  select,
}: {
  page: PortraitSearchPage;
  select: (version: PersonaVersion) => void;
}) {
  return (
    <section aria-label="Portrait search results">
      <p role="status">
        {page.items.length
          ? `${page.items.length} persona${page.items.length === 1 ? "" : "s"} with identical portrait bytes.`
          : "No identical registered portrait found in this workspace."}
      </p>
      {page.has_more && (
        <p>
          Showing the first 20 personas. Additional identical portraits exist.
        </p>
      )}
      <ul>
        {page.items.map((item) => (
          <li key={item.persona_id}>
            <strong>{item.content.name}</strong> · newest matching version{" "}
            {item.revision}{" "}
            <button
              className="secondary"
              aria-label={`Inspect ${item.content.name}, matching version ${item.revision}`}
              onClick={() => select(item)}
            >
              Inspect matching version {item.revision}
            </button>
          </li>
        ))}
      </ul>
      <p className="help">
        Identical file evidence is separate from performer identity and
        production permission.
      </p>
    </section>
  );
}

function MatchedPortrait({
  source,
  candidate,
  denied,
}: {
  source: SavedPersonaSource;
  candidate: PersonaVersion;
  denied: () => void;
}) {
  const { query, state } = useMatchingVersion(source, candidate);
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  return (
    <section aria-label="Matching portrait version">
      <ReadFeedback
        state={state}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {state.phase === "ready" && (
        <>
          <SavedPhoto
            source={source}
            versionId={state.value.version_id}
            name={state.value.content.name}
          />
          <VersionSnapshot version={state.value} />
        </>
      )}
    </section>
  );
}

function useMatchingVersion(
  source: SavedPersonaSource,
  candidate: PersonaVersion,
) {
  const { query, state } = usePersonaQuery<PersonaVersion>();
  useEffect(() => {
    void query.run(async (signal) => {
      const version = await source.gateway.load(
        candidate.persona_id,
        candidate.revision,
        signal,
      );
      requireContract(version.version_id === candidate.version_id);
      return version;
    });
    return () => query.stop();
  }, [source.gateway, candidate, query]);
  return { query, state };
}
