import type {
  DecisionReceipt,
  PersonaVersion,
  ReviewReceipt,
} from "./persona-contracts";

export type GalleryQuery = {
  after_persona_id: string | null;
  limit: number;
  search: string;
};
export type GalleryPage = {
  workspace_id: string;
  items: PersonaVersion[];
  next_after_persona_id: string | null;
};
export type HistoryQuery = { before_ordinal: number | null; limit: number };
export type DecisionPage<T extends ReviewReceipt | DecisionReceipt> = {
  items: T[];
  next_before_ordinal: number | null;
};
export type EvidenceStatus = {
  id: string;
  workspace_id: string;
  version_id: string;
  media_type: "image/png" | "image/jpeg" | "text/plain";
  byte_length: number;
  sha256: string;
  recorded_at: string;
  expires_at: string;
  state: "quarantined" | "clean" | "rejected" | "expired";
};
export const evidenceActions = [
  "persona.review_recorded",
  "persona.campaign_offered",
  "persona.campaign_decided",
] as const;
export type RecordKind = "review" | "campaign_offer" | "campaign_decision";
export type WorkflowEvidence = {
  anchor: {
    record_id: string;
    workspace_id: string;
    version_id: string;
    action: (typeof evidenceActions)[number];
    actor_ref: string;
    recorded_at: string;
    write_request_id: string;
    event_id: string;
  };
  observation_request_id: string;
  cold_event_present: boolean;
  audit_state: "pending" | "entry_present";
  audit_sequence: number | null;
  audit_entry_hash: string | null;
};
