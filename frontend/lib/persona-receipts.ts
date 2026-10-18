import type {
  PersonaDraft,
  PersonaVersion,
  ReviewReceipt,
  DecisionReceipt,
} from "./persona-contracts";
import {
  choice,
  hex,
  integer,
  object,
  text,
  timestamp,
  uuid,
} from "./persona-validation";

export function parseDraft(value: unknown): PersonaDraft {
  const row = object(value, [
    "name",
    "biography",
    "human_contribution",
    "ai_disclosure",
  ]);
  return {
    name: text(row.name, 80),
    biography: text(row.biography, 500),
    human_contribution: text(row.human_contribution, 500),
    ai_disclosure: text(row.ai_disclosure, 500),
  };
}
export function parseVersion(value: unknown): PersonaVersion {
  const row = object(value, [
    "persona_id",
    "workspace_id",
    "version_id",
    "revision",
    "creator_ref",
    "recorded_at",
    "content",
  ]);
  return {
    persona_id: uuid(row.persona_id),
    workspace_id: uuid(row.workspace_id),
    version_id: uuid(row.version_id),
    revision: integer(row.revision),
    creator_ref: text(row.creator_ref, 64),
    recorded_at: timestamp(row.recorded_at),
    content: parseDraft(row.content),
  };
}
export function parseReview(value: unknown): ReviewReceipt {
  const row = object(value, [
    "id",
    "workspace_id",
    "version_id",
    "ordinal",
    "reviewer_ref",
    "decision",
    "statement",
    "recorded_at",
    "event_id",
  ]);
  return {
    id: uuid(row.id),
    workspace_id: uuid(row.workspace_id),
    version_id: uuid(row.version_id),
    ordinal: integer(row.ordinal),
    reviewer_ref: text(row.reviewer_ref, 64),
    decision: choice(row.decision, ["approved", "changes_requested"]),
    statement: text(row.statement, 500),
    recorded_at: timestamp(row.recorded_at),
    event_id: hex(row.event_id, 32),
  };
}
export function parseDecision(value: unknown): DecisionReceipt {
  const row = object(value, [
    "id",
    "workspace_id",
    "campaign_id",
    "ordinal",
    "actor_ref",
    "decision",
    "statement",
    "recorded_at",
    "event_id",
  ]);
  return {
    id: uuid(row.id),
    workspace_id: uuid(row.workspace_id),
    campaign_id: uuid(row.campaign_id),
    ordinal: integer(row.ordinal),
    actor_ref: text(row.actor_ref, 64),
    decision: choice(row.decision, [
      "accepted",
      "changes_requested",
      "revoked",
    ]),
    statement: text(row.statement, 500),
    recorded_at: timestamp(row.recorded_at),
    event_id: hex(row.event_id, 32),
  };
}
