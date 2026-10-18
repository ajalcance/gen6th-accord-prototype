import { useMemo, useState } from "react";
import type { Draft } from "./fixture-data";
import { EXAMPLE_CLOCK } from "./governance-fixtures";
import {
  governancePreview,
  type PreviewCondition,
} from "./governance-preview-transport";
import GovernanceVersions from "./governance-versions";
import GovernanceReviews from "./governance-reviews";
import GovernanceCampaign from "./governance-campaign";
import GovernanceEvidence from "./governance-evidence";
import GovernanceRecovery from "./governance-recovery";

const SECTIONS = [
  "Versions",
  "Reviews",
  "Campaign",
  "Evidence",
  "Save recovery",
] as const;
type Section = (typeof SECTIONS)[number];
type Props = {
  draft: Draft;
  close: () => void;
  connection: () => void;
  creation?: () => void;
};

export default function GovernanceWorkspace(props: Props) {
  const [section, setSection] = useState<Section>("Versions");
  const [condition, setCondition] = useState<PreviewCondition>("normal");
  const gateway = useMemo(() => governancePreview(condition), [condition]);
  return (
    <div className="drawer-body governance-workspace">
      <PreviewNotice />
      <GovernanceNavigation section={section} change={setSection} />
      {section !== "Save recovery" && (
        <PreviewControls condition={condition} setCondition={setCondition} />
      )}
      <div key={`${section}-${condition}`} className="governance-content">
        {section === "Versions" && (
          <GovernanceVersions gateway={gateway} empty={condition === "empty"} />
        )}
        {section === "Reviews" && <GovernanceReviews gateway={gateway} />}
        {section === "Campaign" && (
          <GovernanceCampaign gateway={gateway} empty={condition === "empty"} />
        )}
        {section === "Evidence" && (
          <GovernanceEvidence gateway={gateway} empty={condition === "empty"} />
        )}
        {section === "Save recovery" && <GovernanceRecovery {...props} />}
      </div>
      {condition === "denied" && section !== "Save recovery" && (
        <button className="secondary" onClick={props.connection}>
          Connection details
        </button>
      )}
      {condition === "empty" && section !== "Save recovery" && (
        <div className="button-row">
          {props.creation && (
            <button className="secondary" onClick={props.creation}>
              Go to System Capture
            </button>
          )}
          <button className="secondary" onClick={props.connection}>
            Connection details
          </button>
        </div>
      )}
    </div>
  );
}

function GovernanceNavigation({
  section,
  change,
}: {
  section: Section;
  change: (section: Section) => void;
}) {
  return (
    <div
      className="governance-navigation"
      role="group"
      aria-label="Governance sections"
    >
      {SECTIONS.map((item) => (
        <button
          className="secondary"
          key={item}
          aria-pressed={section === item}
          onClick={() => change(item)}
        >
          {item}
        </button>
      ))}
    </div>
  );
}

function PreviewNotice() {
  return (
    <div className="governance-notice">
      <p className="eyebrow">
        FICTIONAL CONTRACT PREVIEW · NO NETWORK REQUESTS
      </p>
      <h3>Fictional Nova · governance example</h3>
      <p className="help">
        A separate example record shows prepared backend concepts. It is not
        your selected persona or saved server data. All records are unsigned; no
        identity provider, inspection service, monitoring or signing is
        connected.
      </p>
      <details>
        <summary>Example clock & boundaries</summary>
        <p className="help">
          Frozen evaluation time: {EXAMPLE_CLOCK}. Restoring an example does not
          restore real permission or connect a service. Private evidence is
          metadata only; review and acceptance do not establish rights.
        </p>
      </details>
    </div>
  );
}

function PreviewControls({
  condition,
  setCondition,
}: {
  condition: PreviewCondition;
  setCondition: (value: PreviewCondition) => void;
}) {
  return (
    <details className="governance-conditions">
      <summary>Preview conditions</summary>
      <div className="governance-heading">
        <label>
          Read condition
          <select
            value={condition}
            onChange={(event) =>
              setCondition(event.target.value as PreviewCondition)
            }
          >
            <option value="normal">Populated example</option>
            <option value="empty">Empty workspace</option>
            <option value="unavailable">Unavailable service</option>
            <option value="denied">Permission lost</option>
          </select>
        </label>
        {condition !== "normal" && (
          <button className="secondary" onClick={() => setCondition("normal")}>
            Restore populated example
          </button>
        )}
      </div>
      <p className="help">
        Local simulations only. Changing conditions clears the previous read
        view; your browser draft stays intact.
      </p>
    </details>
  );
}
