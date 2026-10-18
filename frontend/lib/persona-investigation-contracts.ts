/** Strict source-bound findings; model output never becomes a permission decision. */
import { parseBox, finite } from "./persona-faces";
import {
  parseQueryReceipt,
  type SearchCommand,
  type QueryReceipt,
} from "./persona-similarity-contracts";
import {
  choice,
  hex,
  integer,
  list,
  object,
  requireContract,
  text,
  timestamp,
  uuid,
} from "./persona-validation";

export const observationLabels = [
  "facial_features_similar",
  "facial_features_different",
  "pose_differs",
  "appearance_differs",
  "comparison_uncertain",
] as const;
export const evidenceGaps = [
  "identity_not_established",
  "rights_not_verified",
  "source_context_unverified",
] as const;
export type InvestigationCommand = SearchCommand & {
  version_id: string;
  portrait_id: string;
  generation_id: string;
  source_note: string;
  retain_findings: true;
};
export type InvestigationResult = {
  id: string;
  workspace_id: string;
  version_id: string;
  portrait_id: string;
  generation_id: string;
  request_id: string;
  ordinal: number;
  actor_ref: string;
  recorded_at: string;
  source_note: string;
  query: QueryReceipt;
  reference_sha256: string;
  reference_face: ReturnType<typeof parseBox>;
  search: ReturnType<typeof parseSearchEvidence>;
  model: string;
  provider_revision: string;
  recipe: "grounded-comparison-v1";
  findings: ReturnType<typeof parseFindings>;
  gaps: (typeof evidenceGaps)[number][];
};
export type InvestigationPage = {
  workspace_id: string;
  version_id: string;
  items: InvestigationResult[];
  next_before_ordinal: number | null;
};
export function parseSearchEvidence(raw: unknown) {
  const r = object(raw, [
    "request_id",
    "method",
    "policy_id",
    "evidence_sha256",
    "scope",
    "face_index",
    "face_cosine",
    "whole_cosine",
  ]);
  return {
    request_id: uuid(r.request_id),
    method: choice(r.method, ["exact-cosine-face-max-v1"]),
    policy_id: text(r.policy_id, 160),
    evidence_sha256: hex(r.evidence_sha256, 64),
    scope: choice(r.scope, ["current", "history"]),
    face_index: boundedIndex(r.face_index),
    face_cosine: finite(r.face_cosine, -1, 1),
    whole_cosine: finite(r.whole_cosine, -1, 1),
  };
}
function boundedIndex(raw: unknown) {
  const n = integer(raw, 0);
  requireContract(n <= 9);
  return n;
}
export function parseFindings(raw: unknown) {
  const r = object(raw, ["state", "observations"]);
  const state = choice(r.state, ["observations", "insufficient_evidence"]);
  const observations = list(
    r.observations,
    (item) => {
      const row = object(item, ["label", "citations"]);
      requireContract(
        Array.isArray(row.citations) &&
          row.citations.join() === "query_image,approved_reference" &&
          row.citations.length === 2,
      );
      return {
        label: choice(row.label, observationLabels),
        citations: ["query_image", "approved_reference"] as const,
      };
    },
    5,
  );
  const labels = observations.map((item) => item.label);
  requireContract(
    new Set(labels).size === labels.length &&
      !!labels.length === (state === "observations") &&
      !(
        labels.includes("facial_features_similar") &&
        labels.includes("facial_features_different")
      ),
  );
  return { state, observations };
}
const packetKeys = [
  "id",
  "workspace_id",
  "version_id",
  "portrait_id",
  "generation_id",
  "request_id",
  "ordinal",
  "actor_ref",
  "recorded_at",
  "source_note",
  "query",
  "reference_sha256",
  "reference_face",
  "search",
  "model",
  "provider_revision",
  "recipe",
  "findings",
  "gaps",
];
export function parseInvestigation(raw: unknown): InvestigationResult {
  const r = object(raw, packetKeys);
  const result: InvestigationResult = {
    id: uuid(r.id),
    workspace_id: uuid(r.workspace_id),
    version_id: uuid(r.version_id),
    portrait_id: uuid(r.portrait_id),
    generation_id: uuid(r.generation_id),
    request_id: uuid(r.request_id),
    ordinal: integer(r.ordinal),
    actor_ref: text(r.actor_ref, 160),
    recorded_at: timestamp(r.recorded_at),
    source_note: text(r.source_note, 500),
    query: parseQueryReceipt(r.query),
    reference_sha256: hex(r.reference_sha256, 64),
    reference_face: parseBox(r.reference_face),
    search: parseSearchEvidence(r.search),
    model: text(r.model, 160),
    provider_revision: text(r.provider_revision, 160),
    recipe: choice(r.recipe, ["grounded-comparison-v1"]),
    findings: parseFindings(r.findings),
    gaps: list(r.gaps, (item) => choice(item, evidenceGaps), 3, 3),
  };
  requireContract(
    result.workspace_id === result.query.workspace_id &&
      result.search.face_index < result.query.faces.length &&
      result.search.request_id === result.request_id &&
      result.gaps.join() === evidenceGaps.join(),
  );
  return result;
}
export function parseInvestigationPage(
  raw: unknown,
  workspace: string,
  version: string,
  before: number | null,
): InvestigationPage {
  const r = object(raw, [
    "workspace_id",
    "version_id",
    "items",
    "next_before_ordinal",
  ]);
  const result = {
    workspace_id: uuid(r.workspace_id),
    version_id: uuid(r.version_id),
    items: list(r.items, parseInvestigation, 20),
    next_before_ordinal:
      r.next_before_ordinal === null ? null : integer(r.next_before_ordinal),
  };
  requireContract(
    result.workspace_id === workspace &&
      result.version_id === version &&
      new Set(result.items.map((item) => item.id)).size === result.items.length,
  );
  result.items.forEach((item, index) =>
    requireContract(
      item.workspace_id === workspace &&
        item.version_id === version &&
        (before === null || item.ordinal < before) &&
        (index === 0 || item.ordinal < result.items[index - 1].ordinal),
    ),
  );
  requireContract(
    result.next_before_ordinal === null ||
      (result.items.length === 20 &&
        result.next_before_ordinal === result.items.at(-1)?.ordinal),
  );
  return result;
}
