import type { StudioState } from "./use-studio";
import CampaignScope from "./campaign-scope";
import {
  CampaignActor,
  RecipientDecision,
  PermissionStatus,
} from "./campaign-decision";

export default function Campaign(props: StudioState) {
  return (
    <>
      <CampaignActor {...props} />
      <div className="campaign-layout">
        <div className="campaign-main">
          <CampaignScope {...props} />
          <RecipientDecision {...props} />
        </div>
        <div className="campaign-aside">
          <PermissionStatus {...props} />
        </div>
      </div>
    </>
  );
}
