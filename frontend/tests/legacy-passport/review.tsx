import type { StudioState } from "./use-studio";
import { ScanWorkspace, ReferenceResults } from "./scan-workspace";
import EvidenceReview from "./review-decision";

export default function Review(props: StudioState) {
  return (
    <div className="review-layout">
      <div className="investigation-column">
        <ScanWorkspace {...props} />
        <ReferenceResults {...props} />
      </div>
      <EvidenceReview {...props} />
    </div>
  );
}
