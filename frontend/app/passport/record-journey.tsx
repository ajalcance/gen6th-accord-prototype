import { useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import type { JourneyPage, RecordNavigation } from "./workspace-pages";
import InvestigationHistory from "./investigation-history";
import { InvestigationReviewRequests } from "./investigation-review-request";
import PreparedReviewWrite from "./prepared-review-write";
import SavedGovernanceReviews from "./saved-governance-reviews";
import SavedGovernanceCampaigns from "./saved-governance-campaigns";
import PreparedCampaignOffer from "./prepared-campaign-offer";
import PreparedCampaignDecision from "./prepared-campaign-decision";
import SavedPassports from "./saved-passports";
import WorkspaceSections from "./workspace-sections";
import ProductionHistory from "./production-history";
import PerformerLifecycle from "./performer-lifecycle";

export type RecordWorkspaceProps = {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
  navigation?: RecordNavigation;
};

export default function RecordJourney(
  props: RecordWorkspaceProps & { page: JourneyPage },
) {
  if (
    props.source.writeGateway &&
    props.source.writeGateway.workspaceId !== props.source.workspaceId
  )
    return <p role="alert">The write connection could not be validated.</p>;
  if (props.page === "Passports")
    return <SavedPassports source={props.source} version={props.version} />;
  return props.page === "Analysis & review" ? (
    <ReviewWorkspace {...props} />
  ) : (
    <ProductionWorkspace {...props} />
  );
}

function ReviewWorkspace(props: RecordWorkspaceProps) {
  const [section, setSection] = useState("Analysis");
  return (
    <>
      <WorkspaceSections
        items={["Analysis", "Independent review", "Rights & operator"]}
        selected={section}
        select={setSection}
        label="Analysis and review sections"
      />
      {section === "Rights & operator" ? (
        <PerformerLifecycle {...props} />
      ) : section === "Analysis" ? (
        <PerformerAnalysis {...props} />
      ) : (
        <IndependentReview {...props} />
      )}
    </>
  );
}
function PerformerAnalysis({
  source,
  version,
  denied,
  navigation,
}: RecordWorkspaceProps) {
  return (
    <section className="workflow-panel" aria-label="Analysis workspace">
      <p className="help">
        Compare a supplied appearance with an approved reference. Findings
        remain separate from a human decision.
      </p>
      <InvestigationHistory
        source={source}
        version={version}
        denied={denied}
        includeReview={false}
        action={
          navigation && (
            <button
              className="text-button"
              onClick={() => navigation.navigate("Records")}
            >
              Find an appearance in Records
            </button>
          )
        }
      />
    </section>
  );
}
function IndependentReview({ source, version, denied }: RecordWorkspaceProps) {
  return (
    <section
      className="workflow-panel workflow-stack"
      aria-label="Independent review workspace"
    >
      <p className="help">
        Review this exact version and evidence you are authorized to access.
        Owner-only attachments are not automatically shared with reviewers.
      </p>
      {source.writeGateway && (
        <PreparedReviewWrite
          source={source}
          version={version}
          denied={denied}
        />
      )}
      <SavedGovernanceReviews gateway={source.gateway} version={version} />
      <InvestigationReviewRequests
        source={source}
        version={version.version_id}
        denied={denied}
      />
    </section>
  );
}
function ProductionWorkspace(props: RecordWorkspaceProps) {
  const [section, setSection] = useState("Current permission");
  const { source, version, denied } = props;
  return (
    <section
      className="workflow-panel workflow-stack"
      aria-label="Production workspace"
    >
      <p className="help">
        Campaign offers, named production roles and recipient decisions for this
        saved version.
      </p>
      <WorkspaceSections
        items={[
          "Current permission",
          "Production history",
          ...(source.writeGateway
            ? ["Create offer", "Recipient decision"]
            : []),
        ]}
        selected={section}
        select={setSection}
        label="Production sections"
      />
      {section === "Current permission" && (
        <SavedGovernanceCampaigns gateway={source.gateway} version={version} />
      )}
      {section === "Production history" && (
        <ProductionHistory gateway={source.gateway} version={version} />
      )}
      {section === "Create offer" && source.writeGateway && (
        <PreparedCampaignOffer
          source={source}
          version={version}
          denied={denied}
        />
      )}
      {section === "Recipient decision" && source.writeGateway && (
        <PreparedCampaignDecision
          source={source}
          version={version}
          denied={denied}
        />
      )}
    </section>
  );
}
