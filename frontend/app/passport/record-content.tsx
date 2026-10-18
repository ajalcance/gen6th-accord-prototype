import { useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { RecordSection } from "./workspace-pages";
import { type RecordWorkspaceProps } from "./record-journey";
import WorkspaceSections from "./workspace-sections";
import SavedPhoto from "./saved-photo";
import SavedCaptures from "./saved-captures";
import EvidenceIntake from "./evidence-intake";
import SavedGovernanceEvidence from "./saved-governance-evidence";
import SavedGovernance from "./saved-governance";
import PreparedVersionWrite from "./prepared-version-write";
import CopyReference from "./copy-reference";
import PerformerIdentity from "./performer-identity";
import PerformerCredits from "./performer-credits";
import PerformerLifecycle from "./performer-lifecycle";

const sections: RecordSection[] = [
  "Overview",
  "References",
  "Evidence & assets",
  "Rights & operator",
  "Activity",
];
export default function RecordContent(
  props: RecordWorkspaceProps & { initialSection?: RecordSection },
) {
  const [section, setSection] = useState<RecordSection>(
    props.initialSection ?? "Overview",
  );
  const { source, version } = props;
  if (
    source.writeGateway &&
    source.writeGateway.workspaceId !== source.workspaceId
  )
    return <p role="alert">The write connection could not be validated.</p>;
  return (
    <>
      <WorkspaceSections
        items={sections}
        selected={section}
        select={(item) => setSection(item as RecordSection)}
        label="Record sections"
      />
      {section === "Overview" && <RecordOverview {...props} />}
      {section === "References" && <RecordReferences {...props} />}
      {section === "Evidence & assets" && <RecordEvidence {...props} />}
      {section === "Rights & operator" && <PerformerLifecycle {...props} />}
      {section === "Activity" && (
        <SavedGovernance source={source} latest={version} />
      )}
    </>
  );
}

function RecordOverview(props: RecordWorkspaceProps) {
  const [editing, setEditing] = useState(false);
  const { source, version, navigation } = props;
  return (
    <>
      <PerformerIdentity version={version} />
      <div className="record-overview">
        <SavedPhoto
          source={source}
          versionId={version.version_id}
          name={version.content.name}
        />
        <VersionDetails version={version} />
      </div>
      <div className="record-detail-actions">
        {source.writeGateway && (
          <button
            className="primary"
            aria-expanded={editing}
            onClick={() => setEditing(!editing)}
          >
            {editing ? "Close editor" : "Edit persona"}
          </button>
        )}
        {navigation && (
          <>
            <button
              className="secondary"
              onClick={() => navigation.navigate("Analysis & review")}
            >
              Analysis &amp; review
            </button>
            <button
              className="secondary"
              onClick={() => navigation.navigate("Production & use")}
            >
              Production &amp; use
            </button>
            <button
              className="secondary"
              onClick={() => navigation.navigate("Passports")}
            >
              Passports
            </button>
          </>
        )}
      </div>
      {editing && source.writeGateway && <PreparedVersionWrite {...props} />}
      <PerformerCredits {...props} />
    </>
  );
}

function VersionDetails({ version }: { version: PersonaVersion }) {
  return (
    <section aria-label="Performer profile">
      <h2>Performer profile</h2>
      <dl className="saved-fields">
        {[
          ["Biography", version.content.biography],
          ["Human contribution", version.content.human_contribution],
          ["AI disclosure", version.content.ai_disclosure],
        ].map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <details className="saved-receipt">
        <summary>Inspect storage receipt</summary>
        <dl className="saved-fields">
          {[
            ["Record ID", version.persona_id],
            ["Version ID", version.version_id],
            ["Recorded at", version.recorded_at],
            ["Creator reference", version.creator_ref],
          ].map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>
                {label.endsWith("ID") ? (
                  <CopyReference label={label} value={value} />
                ) : (
                  value
                )}
              </dd>
            </div>
          ))}
        </dl>
        <p className="help">
          Storage records a claim. Independent review, current production
          permission and passport integrity have their own evidence.
        </p>
      </details>
    </section>
  );
}

function RecordReferences({ source, version, denied }: RecordWorkspaceProps) {
  return (
    <>
      <h2>Capture &amp; approved references</h2>
      {source.captures ? (
        <SavedCaptures
          source={source}
          version={version}
          denied={denied}
          expanded
        />
      ) : (
        <p role="status">
          Capture and reference services are unavailable on this connection.
        </p>
      )}
    </>
  );
}
function RecordEvidence({ source, version, denied }: RecordWorkspaceProps) {
  return source.evidence && source.writeGateway ? (
    <EvidenceIntake
      gateway={source.evidence}
      registry={source.assetRegistry}
      records={source.gateway}
      versionId={version.version_id}
      denied={denied}
    />
  ) : (
    <SavedGovernanceEvidence gateway={source.gateway} version={version} />
  );
}
