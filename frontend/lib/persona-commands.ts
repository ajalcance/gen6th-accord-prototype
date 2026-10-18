import type {
  DecisionCommand,
  OfferCommand,
  ReviewCommand,
  SaveCommand,
} from "./persona-contracts";
import { parseScope } from "./persona-campaign-receipts";
import { parseDraft } from "./persona-receipts";
import {
  choice,
  integer,
  list,
  object,
  requireContract,
  text,
  uuid,
} from "./persona-validation";

function previous(value: unknown): string | null {
  return value === null ? null : uuid(value);
}
export function parseSave(value: unknown): SaveCommand {
  const hasPhoto =
    value !== null &&
    typeof value === "object" &&
    Object.hasOwn(value, "photo");
  const hasReferences =
    value !== null &&
    typeof value === "object" &&
    Object.hasOwn(value, "references");
  const row = object(value, [
    "request_id",
    "content",
    "persona_id",
    "expected_revision",
    ...(hasPhoto ? ["photo"] : []),
    ...(hasReferences ? ["references"] : []),
  ]);
  const id = previous(row.persona_id),
    revision = integer(row.expected_revision, 0);
  requireContract(id !== null || revision === 0);
  return {
    request_id: uuid(row.request_id),
    content: parseDraft(row.content),
    persona_id: id,
    expected_revision: revision,
    ...(hasPhoto ? { photo: parsePhotoChange(row.photo) } : {}),
    ...(hasReferences ? { references: parseReferences(row.references) } : {}),
  };
}
function parseReferences(
  value: unknown,
): NonNullable<SaveCommand["references"]> {
  const row = object(value, ["action", "upload_ids"]);
  const action = choice(row.action, ["keep", "replace"]),
    upload_ids = list(row.upload_ids, uuid, 8);
  requireContract(
    new Set(upload_ids).size === upload_ids.length &&
      (action !== "keep" || !upload_ids.length),
  );
  return { action, upload_ids };
}
function parsePhotoChange(value: unknown): NonNullable<SaveCommand["photo"]> {
  const row = object(value, ["action", "upload_id"]);
  const action = choice(row.action, ["keep", "remove", "attach"]);
  if (action === "attach") return { action, upload_id: uuid(row.upload_id) };
  requireContract(row.upload_id === null);
  return { action, upload_id: null };
}
export function parseReviewCommand(value: unknown): ReviewCommand {
  const row = object(value, [
    "request_id",
    "version_id",
    "expected_previous_id",
    "decision",
    "statement",
  ]);
  return {
    request_id: uuid(row.request_id),
    version_id: uuid(row.version_id),
    expected_previous_id: previous(row.expected_previous_id),
    decision: choice(row.decision, ["approved", "changes_requested"]),
    statement: text(row.statement, 500),
  };
}
export function parseOffer(value: unknown): OfferCommand {
  const row = object(value, ["request_id", "version_id", "review_id", "scope"]);
  return {
    request_id: uuid(row.request_id),
    version_id: uuid(row.version_id),
    review_id: uuid(row.review_id),
    scope: parseScope(row.scope),
  };
}
export function parseDecisionCommand(value: unknown): DecisionCommand {
  const row = object(value, [
    "request_id",
    "campaign_id",
    "expected_previous_id",
    "decision",
    "statement",
  ]);
  return {
    request_id: uuid(row.request_id),
    campaign_id: uuid(row.campaign_id),
    expected_previous_id: previous(row.expected_previous_id),
    decision: choice(row.decision, [
      "accepted",
      "changes_requested",
      "revoked",
    ]),
    statement: text(row.statement, 500),
  };
}
