/** Persona version and workflow shapes. Identity is never a command field. */
import type { ProductionUse } from "./persona-production";
export type PersonaDraft = {
  name: string;
  biography: string;
  human_contribution: string;
  ai_disclosure: string;
};
export type PersonaVersion = {
  persona_id: string;
  workspace_id: string;
  version_id: string;
  revision: number;
  creator_ref: string;
  recorded_at: string;
  content: PersonaDraft;
};
export type SaveCommand = {
  request_id: string;
  content: PersonaDraft;
  persona_id: string | null;
  expected_revision: number;
  photo?: PhotoChange;
  references?: { action: "keep" | "replace"; upload_ids: string[] };
};
export type PhotoChange =
  | { action: "keep" | "remove"; upload_id: null }
  | { action: "attach"; upload_id: string };
export type ReviewCommand = {
  request_id: string;
  version_id: string;
  expected_previous_id: string | null;
  decision: "approved" | "changes_requested";
  statement: string;
};
export type ReviewReceipt = {
  id: string;
  workspace_id: string;
  version_id: string;
  ordinal: number;
  reviewer_ref: string;
  decision: ReviewCommand["decision"];
  statement: string;
  recorded_at: string;
  event_id: string;
};
export type CampaignScope = {
  name: string;
  recipient_ref: string;
  asset_ids: string[];
  purpose: string;
  conditions: string;
  starts_at: string;
  ends_at: string;
  production?: ProductionUse;
};
export type OfferCommand = {
  request_id: string;
  version_id: string;
  review_id: string;
  scope: CampaignScope;
};
export type CampaignReceipt = {
  id: string;
  workspace_id: string;
  version_id: string;
  review_id: string;
  owner_ref: string;
  scope: CampaignScope;
  assets: { id: string; digest: string; label: string }[];
  recorded_at: string;
  event_id: string;
};
export type DecisionCommand = {
  request_id: string;
  campaign_id: string;
  expected_previous_id: string | null;
  decision: "accepted" | "changes_requested" | "revoked";
  statement: string;
};
export type DecisionReceipt = {
  id: string;
  workspace_id: string;
  campaign_id: string;
  ordinal: number;
  actor_ref: string;
  decision: DecisionCommand["decision"];
  statement: string;
  recorded_at: string;
  event_id: string;
};
export const blockingReasons = [
  "stale_version",
  "review_changed",
  "reviewer_permission_removed",
  "owner_permission_removed",
  "recipient_permission_removed",
  "awaiting_acceptance",
  "changes_requested",
  "revoked",
  "not_started",
  "expired",
  "supporting_evidence_unavailable",
  "lifecycle_unavailable",
  "performer_suspended",
  "governance_missing",
  "governance_changed",
  "operator_unavailable",
  "governance_review_required",
  "governance_expired",
  "rights_window_unavailable",
  "voice_rights_missing",
] as const;
export type CampaignStatus = {
  receipt: CampaignReceipt;
  latest_decision: DecisionReceipt | null;
  evaluated_at: string;
  blocking_reasons: (typeof blockingReasons)[number][];
  eligible_for_use: boolean;
};
