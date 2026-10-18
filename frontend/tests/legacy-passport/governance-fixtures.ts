/** Fixed fictional contract examples, separate from editable browser personas and server records. */
import type {
  CampaignReceipt,
  DecisionReceipt,
  PersonaVersion,
  ReviewReceipt,
} from "../../lib/persona-contracts";
import type {
  EvidenceStatus,
  WorkflowEvidence,
} from "../../lib/persona-read-contracts";

export const exampleId = (n: number) =>
  `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
export const EXAMPLE_WORKSPACE = exampleId(101);
export const EXAMPLE_PERSONA = exampleId(102);
export const EXAMPLE_CLOCK = "2026-10-03T00:00:00Z";
export const EXAMPLE_VERSIONS: PersonaVersion[] = [3, 2, 1].map((revision) => ({
  persona_id: EXAMPLE_PERSONA,
  workspace_id: EXAMPLE_WORKSPACE,
  version_id: exampleId(110 + revision),
  revision,
  creator_ref: "fictional-creator",
  recorded_at: `2026-10-02T0${revision}:00:00Z`,
  content: {
    name: "Fictional Nova · governance example",
    biography:
      revision === 1
        ? "A fictional editorial character."
        : "A fictional editorial character with a documented palette study.",
    human_contribution:
      revision === 3
        ? "Original concept, composition and hand-edited palette; references listed."
        : "Original concept and hand-edited palette.",
    ai_disclosure:
      "Synthetic workflow example; no AI model or real upload ran.",
  },
}));
export const EXAMPLE_REVIEW_VERSION = EXAMPLE_VERSIONS[1];
export const EXAMPLE_REVIEWS: ReviewReceipt[] = [
  {
    id: exampleId(122),
    workspace_id: EXAMPLE_WORKSPACE,
    version_id: EXAMPLE_REVIEW_VERSION.version_id,
    ordinal: 2,
    reviewer_ref: "fictional-reviewer",
    decision: "approved",
    statement:
      "The example disclosure addresses the requested clarification. This is not a rights determination.",
    recorded_at: "2026-10-02T02:20:00Z",
    event_id: "a".repeat(32),
  },
  {
    id: exampleId(121),
    workspace_id: EXAMPLE_WORKSPACE,
    version_id: EXAMPLE_REVIEW_VERSION.version_id,
    ordinal: 1,
    reviewer_ref: "fictional-reviewer",
    decision: "changes_requested",
    statement:
      "Clarify the example reference source and the human edits before review.",
    recorded_at: "2026-10-02T02:10:00Z",
    event_id: "b".repeat(32),
  },
];
export const EXAMPLE_CAMPAIGN: CampaignReceipt = {
  id: exampleId(130),
  workspace_id: EXAMPLE_WORKSPACE,
  version_id: EXAMPLE_REVIEW_VERSION.version_id,
  review_id: EXAMPLE_REVIEWS[0].id,
  owner_ref: "fictional-creator",
  scope: {
    name: "Fictional editorial campaign",
    recipient_ref: "fictional-recipient",
    asset_ids: [exampleId(131)],
    purpose: "One fictional editorial placement.",
    conditions: "No sublicensing or private-evidence use.",
    starts_at: "2026-10-02T02:30:00Z",
    ends_at: "2026-10-04T02:30:00Z",
  },
  assets: [
    {
      id: exampleId(131),
      digest: "c".repeat(64),
      label: "Fictional campaign illustration",
    },
  ],
  recorded_at: "2026-10-02T02:30:00Z",
  event_id: "c".repeat(32),
};
export const EXAMPLE_DECISIONS: DecisionReceipt[] = [
  {
    id: exampleId(143),
    workspace_id: EXAMPLE_WORKSPACE,
    campaign_id: EXAMPLE_CAMPAIGN.id,
    ordinal: 3,
    actor_ref: "fictional-creator",
    decision: "revoked",
    statement: "The example offer is revoked following a new version.",
    recorded_at: "2026-10-02T03:10:00Z",
    event_id: "d".repeat(32),
  },
  {
    id: exampleId(142),
    workspace_id: EXAMPLE_WORKSPACE,
    campaign_id: EXAMPLE_CAMPAIGN.id,
    ordinal: 2,
    actor_ref: "fictional-recipient",
    decision: "accepted",
    statement: "Accept only this fictional scope and its named asset.",
    recorded_at: "2026-10-02T02:50:00Z",
    event_id: "e".repeat(32),
  },
  {
    id: exampleId(141),
    workspace_id: EXAMPLE_WORKSPACE,
    campaign_id: EXAMPLE_CAMPAIGN.id,
    ordinal: 1,
    actor_ref: "fictional-recipient",
    decision: "changes_requested",
    statement: "Clarify the fictional use conditions.",
    recorded_at: "2026-10-02T02:40:00Z",
    event_id: "f".repeat(32),
  },
];
export const EXAMPLE_EVIDENCE: EvidenceStatus[] = (
  ["quarantined", "clean", "rejected", "expired"] as const
).map((state, i) => ({
  id: exampleId(150 + i),
  workspace_id: EXAMPLE_WORKSPACE,
  version_id: EXAMPLE_REVIEW_VERSION.version_id,
  media_type: "text/plain",
  byte_length: 48,
  sha256: String(i + 1).repeat(64),
  recorded_at:
    state === "expired" ? "2026-09-25T02:00:00Z" : "2026-10-02T02:00:00Z",
  expires_at:
    state === "expired" ? "2026-10-02T02:00:00Z" : "2026-10-09T02:00:00Z",
  state,
}));

export function exampleAudit(recordId: string): WorkflowEvidence {
  const review = EXAMPLE_REVIEWS.find((row) => row.id === recordId);
  const decision = EXAMPLE_DECISIONS.find((row) => row.id === recordId);
  if (!review && !decision) throw new Error("Unknown fictional audit record");
  const row = review ?? decision!;
  const present = row.ordinal === 1;
  return {
    anchor: {
      record_id: row.id,
      workspace_id: EXAMPLE_WORKSPACE,
      version_id: EXAMPLE_REVIEW_VERSION.version_id,
      action: review ? "persona.review_recorded" : "persona.campaign_decided",
      actor_ref: review ? review.reviewer_ref : decision!.actor_ref,
      recorded_at: row.recorded_at,
      write_request_id: exampleId(200 + row.ordinal + (review ? 0 : 10)),
      event_id: row.event_id,
    },
    observation_request_id: exampleId(220),
    cold_event_present: true,
    audit_state: present ? "entry_present" : "pending",
    audit_sequence: present ? 1 : null,
    audit_entry_hash: present ? "a".repeat(64) : null,
  };
}
