import { useMemo, useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { CaptureProfile } from "../../lib/persona-captures";
import type { SavedPersonaSource } from "./saved-source";
import { CaptureSummary, useCaptureProfile } from "./capture-status";
import { ReadFeedback } from "./saved-record";
import ReferencePhoto from "./reference-photo";
import ReferenceEditor from "./reference-editor";
import FaceInspection from "./face-inspection";

export type ReferenceProps = {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
};
export default function SavedCaptures(
  props: ReferenceProps & { expanded?: boolean },
) {
  const [open, setOpen] = useState(false);
  if (!props.source.captures) return null;
  return (
    <section className="reference-set" aria-label="Capture and references">
      {!props.expanded && (
        <button
          type="button"
          className="secondary"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {open
            ? "Close capture and references"
            : "Inspect capture and references"}
        </button>
      )}
      {(open || props.expanded) && <CaptureContent {...props} />}
    </section>
  );
}
function CaptureContent(props: ReferenceProps) {
  const { source, version, denied } = props;
  const command = useMemo(
    () => ({ upload_id: null, version_id: version.version_id }),
    [version.version_id],
  );
  const { query, state, available } = useCaptureProfile(
    source,
    command,
    undefined,
    denied,
  );
  if (!available)
    return (
      <p role="alert">Capture access is unavailable for this workspace.</p>
    );
  return (
    <>
      <ReadFeedback
        state={state}
        resource="Capture profile"
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {state.phase === "ready" && (
        <CaptureReady {...props} profile={state.value} />
      )}
    </>
  );
}
function CaptureReady(props: ReferenceProps & { profile: CaptureProfile }) {
  const { source, version, profile } = props;
  const [editing, setEditing] = useState(false);
  return (
    <>
      <CaptureSummary capture={profile.capture} />
      <h3>Approved references · version {version.revision}</h3>
      <p className="help">
        These portraits are the studio-approved reference set for this version.
        Inspect face processing separately for each approved reference.
      </p>
      <CaptureReferences {...props} />
      {source.writeGateway?.workspaceId === source.workspaceId && (
        <button
          type="button"
          className="secondary"
          aria-expanded={editing}
          onClick={() => setEditing(!editing)}
        >
          {editing ? "Close reference editor" : "Edit approved references"}
        </button>
      )}
      {editing && (
        <ReferenceEditor {...props} references={profile.references} />
      )}
    </>
  );
}
function CaptureReferences({
  source,
  version,
  denied,
  profile,
}: ReferenceProps & { profile: CaptureProfile }) {
  if (!profile.references.length)
    return <p>No references approved for this version.</p>;
  return (
    <ol className="reference-cards">
      {profile.references.map((item) => (
        <li key={item.portrait_id}>
          <ReferencePhoto
            gateway={source.captures!}
            version={version.version_id}
            portrait={item.portrait_id}
            denied={denied}
          />
          <CaptureSummary capture={item} />
          <FaceInspection
            source={source}
            version={version}
            denied={denied}
            capture={item}
          />
        </li>
      ))}
    </ol>
  );
}
