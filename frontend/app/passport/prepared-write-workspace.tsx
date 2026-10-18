import { useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import type { WriteKind } from "./prepared-write-state";
import PreparedVersionWrite from "./prepared-version-write";
import PreparedReviewWrite from "./prepared-review-write";
import PreparedCampaignOffer from "./prepared-campaign-offer";
import PreparedCampaignDecision from "./prepared-campaign-decision";

const actions: { kind: WriteKind; label: string }[] = [
  { kind: "save", label: "Edit version" },
  { kind: "review", label: "Independent review" },
  { kind: "offer", label: "Offer campaign" },
  { kind: "decide", label: "Decide campaign" },
];
export default function PreparedWriteWorkspace({
  source,
  version,
  denied,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
}) {
  const [kind, setKind] = useState<WriteKind>("save");
  if (!source.writeGateway) return null;
  if (
    source.writeGateway.workspaceId !== source.workspaceId ||
    version.workspace_id !== source.workspaceId
  )
    return (
      <p role="alert">The prepared write workspace could not be validated.</p>
    );
  const props = { source, version, denied };
  return (
    <section
      className="governance-section prepared-writes"
      aria-label="Record actions"
    >
      <p className="help">
        Record actions · server authorization required · unsigned. Review each
        action before submitting it.
      </p>
      <nav className="governance-navigation" aria-label="Prepared action">
        {actions.map((action) => (
          <button
            className="secondary"
            key={action.kind}
            aria-pressed={kind === action.kind}
            onClick={() => setKind(action.kind)}
          >
            {action.label}
          </button>
        ))}
      </nav>
      {kind === "save" && <PreparedVersionWrite {...props} />}
      {kind === "review" && <PreparedReviewWrite {...props} />}
      {kind === "offer" && <PreparedCampaignOffer {...props} />}
      {kind === "decide" && <PreparedCampaignDecision {...props} />}
    </section>
  );
}
