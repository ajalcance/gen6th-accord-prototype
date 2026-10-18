/** Browser-only example transport. It cannot read HTTP, credentials, storage or real evidence. */
import { ApiError } from "../../lib/api-client";
import {
  personaGateway,
  PersonaDisconnectedError,
  type PersonaTransport,
} from "../../lib/persona-gateway";
import { requireContract } from "../../lib/persona-validation";
import {
  EXAMPLE_CAMPAIGN,
  EXAMPLE_CLOCK,
  EXAMPLE_DECISIONS,
  EXAMPLE_EVIDENCE,
  EXAMPLE_PERSONA,
  EXAMPLE_REVIEWS,
  EXAMPLE_VERSIONS,
  EXAMPLE_WORKSPACE,
  exampleAudit,
} from "./governance-fixtures";

export type PreviewCondition = "normal" | "empty" | "unavailable" | "denied";

function examplePage<T extends { ordinal: number }>(
  rows: T[],
  body: Record<string, unknown>,
) {
  const before = body.before_ordinal;
  const filtered = rows.filter(
    (row) =>
      before === null || (typeof before === "number" && row.ordinal < before),
  );
  const limit = typeof body.limit === "number" ? body.limit : 1;
  const items = filtered.slice(0, limit);
  return {
    items,
    next_before_ordinal: filtered.length > limit ? items.at(-1)!.ordinal : null,
  };
}

function previewResponse(
  operation: Parameters<PersonaTransport>[0],
  body: Record<string, unknown>,
  empty: boolean,
) {
  if (operation === "load") {
    requireContract(body.persona_id === EXAMPLE_PERSONA);
    const result = EXAMPLE_VERSIONS.find(
      (row) => body.revision === null || row.revision === body.revision,
    );
    requireContract(result);
    return result;
  }
  if (operation === "reviewHistory") {
    requireContract(
      EXAMPLE_VERSIONS.some((row) => row.version_id === body.version_id),
    );
    return examplePage(
      empty
        ? []
        : EXAMPLE_REVIEWS.filter((row) => row.version_id === body.version_id),
      body,
    );
  }
  if (operation === "campaignHistory") {
    requireContract(body.campaign_id === EXAMPLE_CAMPAIGN.id);
    return examplePage(empty ? [] : EXAMPLE_DECISIONS, body);
  }
  if (operation === "campaignStatus") {
    requireContract(body.campaign_id === EXAMPLE_CAMPAIGN.id);
    return {
      receipt: EXAMPLE_CAMPAIGN,
      latest_decision: EXAMPLE_DECISIONS[0],
      evaluated_at: EXAMPLE_CLOCK,
      blocking_reasons: ["revoked", "stale_version"],
      eligible_for_use: false,
    };
  }
  if (operation === "evidenceStatus") {
    const row = EXAMPLE_EVIDENCE.find((item) => item.id === body.evidence_id);
    requireContract(row);
    return row;
  }
  if (operation === "workflowEvidence") {
    requireContract(typeof body.record_id === "string");
    return exampleAudit(body.record_id);
  }
  throw new PersonaDisconnectedError();
}

export function governancePreview(condition: PreviewCondition = "normal") {
  const transport: PersonaTransport = async (
    operation,
    workspace,
    command,
    signal,
  ) => {
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    requireContract(
      workspace === EXAMPLE_WORKSPACE &&
        command !== null &&
        typeof command === "object",
    );
    if (condition === "unavailable")
      throw new ApiError("Fictional unavailable service", 503);
    if (condition === "denied")
      throw new ApiError("Fictional permission loss", 403);
    return structuredClone(
      previewResponse(
        operation,
        command as Record<string, unknown>,
        condition === "empty",
      ),
    );
  };
  return personaGateway(EXAMPLE_WORKSPACE, transport);
}
