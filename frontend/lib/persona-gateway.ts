/** Prepared adapter only: no HTTP routes or trusted identity connection are activated. */
import type {
  DecisionCommand,
  OfferCommand,
  ReviewCommand,
  SaveCommand,
} from "./persona-contracts";
import {
  parseCampaign,
  parseCampaignStatus,
} from "./persona-campaign-receipts";
import {
  parseDecisionCommand,
  parseOffer,
  parseReviewCommand,
  parseSave,
} from "./persona-commands";
import { parseDecision, parseReview, parseVersion } from "./persona-receipts";
import { integer, requireContract, uuid } from "./persona-validation";
import { PersonaReads } from "./persona-reads";
import { PersonaGovernanceReads } from "./persona-governance-reads";

export type PersonaOperation =
  | "load"
  | "save"
  | "review"
  | "offer"
  | "decide"
  | "campaignStatus"
  | "gallery"
  | "reviewHistory"
  | "campaignHistory"
  | "evidenceStatus"
  | "workflowEvidence"
  | "versionHistory"
  | "campaignOffers"
  | "evidenceList";
/** A future session-bound transport must enforce server-side attribution and authorization. */
export type PersonaTransport = (
  operation: PersonaOperation,
  workspace: string,
  command: unknown,
  signal?: AbortSignal,
) => Promise<unknown>;
export class PersonaDisconnectedError extends Error {
  constructor() {
    super("Persona API is not connected.");
  }
}
const disconnected: PersonaTransport = async () => {
  throw new PersonaDisconnectedError();
};

export class PersonaGateway {
  private readonly workspace: string;
  get workspaceId(): string {
    return this.workspace;
  }
  readonly reads: PersonaReads;
  readonly governance: PersonaGovernanceReads;
  constructor(
    workspaceId: string,
    private readonly transport: PersonaTransport = disconnected,
  ) {
    this.workspace = uuid(workspaceId);
    this.reads = new PersonaReads(this.workspace, transport);
    this.governance = new PersonaGovernanceReads(this.workspace, transport);
  }
  private async invoke<T extends { workspace_id: string }>(
    operation: PersonaOperation,
    command: unknown,
    parse: (data: unknown) => T,
    signal?: AbortSignal,
  ): Promise<T> {
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    const raw = await this.transport(
      operation,
      this.workspace,
      command,
      signal,
    );
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    const result = parse(raw);
    requireContract(result.workspace_id === this.workspace);
    return result;
  }
  async load(
    personaId: string,
    revision: number | null = null,
    signal?: AbortSignal,
  ) {
    const id = uuid(personaId);
    const result = await this.invoke(
      "load",
      {
        persona_id: id,
        revision: revision === null ? null : integer(revision),
      },
      parseVersion,
      signal,
    );
    requireContract(
      result.persona_id === id &&
        (revision === null || result.revision === revision),
    );
    return result;
  }
  async save(command: SaveCommand, signal?: AbortSignal) {
    const body = parseSave(command);
    const result = await this.invoke("save", body, parseVersion, signal);
    requireContract(
      (body.persona_id === null || result.persona_id === body.persona_id) &&
        result.revision === body.expected_revision + 1,
    );
    requireContract(
      JSON.stringify(result.content) === JSON.stringify(body.content),
    );
    return result;
  }
  async review(command: ReviewCommand, signal?: AbortSignal) {
    const body = parseReviewCommand(command);
    const result = await this.invoke("review", body, parseReview, signal);
    requireContract(
      result.version_id === body.version_id &&
        result.id !== body.expected_previous_id &&
        (body.expected_previous_id === null
          ? result.ordinal === 1
          : result.ordinal > 1) &&
        result.decision === body.decision &&
        result.statement === body.statement,
    );
    return result;
  }
  async offer(command: OfferCommand, signal?: AbortSignal) {
    const body = parseOffer(command);
    const result = await this.invoke("offer", body, parseCampaign, signal);
    requireContract(
      result.version_id === body.version_id &&
        result.review_id === body.review_id &&
        JSON.stringify(result.scope) === JSON.stringify(body.scope),
    );
    return result;
  }
  async decide(command: DecisionCommand, signal?: AbortSignal) {
    const body = parseDecisionCommand(command);
    const result = await this.invoke("decide", body, parseDecision, signal);
    requireContract(
      result.campaign_id === body.campaign_id &&
        result.id !== body.expected_previous_id &&
        (body.expected_previous_id === null
          ? result.ordinal === 1
          : result.ordinal > 1) &&
        result.decision === body.decision &&
        result.statement === body.statement,
    );
    return result;
  }
  async campaignStatus(campaignId: string, signal?: AbortSignal) {
    const id = uuid(campaignId);
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    const raw = await this.transport(
      "campaignStatus",
      this.workspace,
      { campaign_id: id },
      signal,
    );
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    const result = parseCampaignStatus(raw);
    requireContract(
      result.receipt.workspace_id === this.workspace &&
        result.receipt.id === id,
    );
    return result;
  }
}

export function personaGateway(
  workspaceId: string,
  transport?: PersonaTransport,
): PersonaGateway {
  return new PersonaGateway(workspaceId, transport);
}
