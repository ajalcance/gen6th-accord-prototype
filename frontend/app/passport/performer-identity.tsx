import type { PersonaVersion } from "../../lib/persona-contracts";
import CopyReference from "./copy-reference";
import { RecordedTime } from "./governance-common";

export default function PerformerIdentity({
  version,
}: {
  version: PersonaVersion;
}) {
  return (
    <section
      className="performer-identity"
      aria-label="Performer identity and attribution"
    >
      <div>
        <h2>Performer identity</h2>
        <p className="help">
          This ID continues across saved names and appearance versions.
        </p>
      </div>
      <dl className="saved-fields">
        <div>
          <dt>Performer ID</dt>
          <dd>
            <CopyReference label="Performer ID" value={version.persona_id} />
          </dd>
        </div>
        <div>
          <dt>Profile source</dt>
          <dd>
            Creator declared · <RecordedTime value={version.recorded_at} />
          </dd>
        </div>
      </dl>
      <details>
        <summary>What this record establishes</summary>
        <p>
          Biography, human contribution and AI disclosure were supplied by{" "}
          {version.creator_ref} for version {version.revision}. Receipt time
          records submission, not original creation.
        </p>
        <p className="help">
          Portrait inspection, approved references, independent review, current
          production permission and passport integrity have separate supporting
          records. Registration does not automatically publish this profile.
        </p>
        <dl className="saved-fields">
          <div>
            <dt>Workspace scope</dt>
            <dd>{version.workspace_id}</dd>
          </div>
        </dl>
      </details>
    </section>
  );
}
