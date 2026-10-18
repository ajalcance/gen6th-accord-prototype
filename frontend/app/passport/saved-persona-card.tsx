import type { PersonaVersion } from "../../lib/persona-contracts";
import Icon from "./icons";
import SavedPhoto from "./saved-photo";
import { useSavedSource } from "./saved-source";

export default function SavedPersonaCard({
  version,
  open,
}: {
  version: PersonaVersion;
  open: () => void;
}) {
  const recorded = new Date(version.recorded_at);
  const source = useSavedSource();
  return (
    <button
      className="saved-card"
      onClick={open}
      aria-label={`Open record ${version.content.name}`}
    >
      <SavedPhoto
        source={source}
        versionId={version.version_id}
        name={version.content.name}
      >
        <span className="saved-card-title">{version.content.name}</span>
      </SavedPhoto>
      <span className="saved-card-excerpt">{version.content.biography}</span>
      <span className="saved-card-meta">
        <span className="card-state">v{version.revision}</span>
        <time dateTime={version.recorded_at} title={recorded.toLocaleString()}>
          Saved{" "}
          {recorded.toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
          })}
        </time>
      </span>
      <span className="saved-card-footer">
        <span className="card-state">Saved record</span>
        <span className="card-open">
          Open record <Icon name="arrow" size={14} />
        </span>
      </span>
    </button>
  );
}
