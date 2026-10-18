import {
  blockingReasons,
  type CampaignReceipt,
  type CampaignScope,
  type CampaignStatus,
} from "./persona-contracts";
import { parseDecision } from "./persona-receipts";
import { parseProduction } from "./persona-production";
import {
  choice,
  hex,
  list,
  object,
  requireContract,
  text,
  timestamp,
  uuid,
} from "./persona-validation";

export function parseScope(value: unknown): CampaignScope {
  const production =
    value !== null &&
    typeof value === "object" &&
    Object.hasOwn(value, "production");
  const row = object(value, [
    "name",
    "recipient_ref",
    "asset_ids",
    "purpose",
    "conditions",
    "starts_at",
    "ends_at",
    ...(production ? ["production"] : []),
  ]);
  const ids = list(row.asset_ids, uuid, 20, 1);
  requireContract(new Set(ids).size === ids.length);
  const starts = new Date(timestamp(row.starts_at)).toISOString(),
    ends = new Date(timestamp(row.ends_at)).toISOString();
  const duration = Date.parse(ends) - Date.parse(starts);
  requireContract(duration > 0 && duration <= 366 * 86400000);
  const parsedProduction = production
    ? parseProduction(row.production)
    : undefined;
  requireContract(
    parsedProduction?.use_mode !== "trial" || duration <= 30 * 86400000,
  );
  return {
    name: text(row.name, 80),
    recipient_ref: text(row.recipient_ref, 64),
    asset_ids: [...ids].sort(),
    purpose: text(row.purpose, 500),
    conditions: text(row.conditions, 500),
    starts_at: starts,
    ends_at: ends,
    ...(production ? { production: parsedProduction } : {}),
  };
}
function parseAsset(value: unknown): CampaignReceipt["assets"][number] {
  const row = object(value, ["id", "digest", "label"]);
  return {
    id: uuid(row.id),
    digest: hex(row.digest, 64),
    label: text(row.label, 80),
  };
}
export function parseCampaign(value: unknown): CampaignReceipt {
  const row = object(value, [
    "id",
    "workspace_id",
    "version_id",
    "review_id",
    "owner_ref",
    "scope",
    "assets",
    "recorded_at",
    "event_id",
  ]);
  const scope = parseScope(row.scope),
    assets = list(row.assets, parseAsset, 20, 1);
  const owner = text(row.owner_ref, 64);
  requireContract(
    owner !== scope.recipient_ref && assets.length === scope.asset_ids.length,
  );
  requireContract(
    assets.every((asset, index) => asset.id === scope.asset_ids[index]),
  );
  return {
    id: uuid(row.id),
    workspace_id: uuid(row.workspace_id),
    version_id: uuid(row.version_id),
    review_id: uuid(row.review_id),
    owner_ref: owner,
    scope,
    assets,
    recorded_at: timestamp(row.recorded_at),
    event_id: hex(row.event_id, 32),
  };
}
export function parseCampaignStatus(value: unknown): CampaignStatus {
  const row = object(value, [
    "receipt",
    "latest_decision",
    "evaluated_at",
    "blocking_reasons",
    "eligible_for_use",
  ]);
  const receipt = parseCampaign(row.receipt);
  const decision =
    row.latest_decision === null ? null : parseDecision(row.latest_decision);
  const evaluated = timestamp(row.evaluated_at);
  const reasons = list(
    row.blocking_reasons,
    (item) => choice(item, blockingReasons),
    blockingReasons.length,
  );
  requireContract(typeof row.eligible_for_use === "boolean");
  requireContract(row.eligible_for_use === (reasons.length === 0));
  if (decision) {
    requireContract(
      decision.campaign_id === receipt.id &&
        decision.workspace_id === receipt.workspace_id,
    );
    requireContract(
      decision.actor_ref ===
        (decision.decision === "revoked"
          ? receipt.owner_ref
          : receipt.scope.recipient_ref),
    );
  }
  if (row.eligible_for_use) {
    requireContract(decision?.decision === "accepted");
    requireContract(
      Date.parse(receipt.scope.starts_at) <= Date.parse(evaluated) &&
        Date.parse(evaluated) < Date.parse(receipt.scope.ends_at),
    );
  }
  return {
    receipt,
    latest_decision: decision,
    evaluated_at: evaluated,
    blocking_reasons: reasons,
    eligible_for_use: row.eligible_for_use,
  };
}
