/** Authorized read shapes; transport/session enforcement remains a server prerequisite. */
import type { PersonaTransport } from "./persona-gateway";
import type {
  GalleryQuery,
  HistoryQuery,
  RecordKind,
} from "./persona-read-contracts";
import {
  parseGalleryPage,
  parseGalleryQuery,
  parseHistoryQuery,
  parseDecisionPage,
} from "./persona-pages";
import { parseDecision, parseReview } from "./persona-receipts";
import {
  parseEvidenceStatus,
  parseWorkflowEvidence,
} from "./persona-evidence-receipts";
import { choice, requireContract, uuid } from "./persona-validation";

export class PersonaReads {
  constructor(
    private readonly workspace: string,
    private readonly transport: PersonaTransport,
  ) {}

  private async receive(
    operation: Parameters<PersonaTransport>[0],
    command: unknown,
    signal?: AbortSignal,
  ): Promise<unknown> {
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    const data = await this.transport(
      operation,
      this.workspace,
      command,
      signal,
    );
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    return data;
  }
  async gallery(query: GalleryQuery, signal?: AbortSignal) {
    const command = parseGalleryQuery(query);
    const raw = await this.receive("gallery", command, signal);
    return parseGalleryPage(raw, this.workspace, command);
  }
  async reviewHistory(
    versionId: string,
    query: HistoryQuery,
    signal?: AbortSignal,
  ) {
    const id = uuid(versionId),
      page = parseHistoryQuery(query);
    const raw = await this.receive(
      "reviewHistory",
      { version_id: id, ...page },
      signal,
    );
    return parseDecisionPage(
      raw,
      page,
      parseReview,
      (item) => item.workspace_id === this.workspace && item.version_id === id,
    );
  }
  async campaignHistory(
    campaignId: string,
    query: HistoryQuery,
    signal?: AbortSignal,
  ) {
    const id = uuid(campaignId),
      page = parseHistoryQuery(query);
    const raw = await this.receive(
      "campaignHistory",
      { campaign_id: id, ...page },
      signal,
    );
    return parseDecisionPage(
      raw,
      page,
      parseDecision,
      (item) => item.workspace_id === this.workspace && item.campaign_id === id,
    );
  }
  async evidenceStatus(evidenceId: string, signal?: AbortSignal) {
    const id = uuid(evidenceId);
    const result = parseEvidenceStatus(
      await this.receive("evidenceStatus", { evidence_id: id }, signal),
    );
    requireContract(result.workspace_id === this.workspace && result.id === id);
    return result;
  }
  async workflowEvidence(
    recordId: string,
    kind: RecordKind,
    signal?: AbortSignal,
  ) {
    const id = uuid(recordId);
    const checkedKind = choice(kind, [
      "review",
      "campaign_offer",
      "campaign_decision",
    ]);
    const raw = await this.receive(
      "workflowEvidence",
      { record_id: id, kind: checkedKind },
      signal,
    );
    const result = parseWorkflowEvidence(raw);
    const actions = {
      review: "persona.review_recorded",
      campaign_offer: "persona.campaign_offered",
      campaign_decision: "persona.campaign_decided",
    };
    requireContract(
      result.anchor.workspace_id === this.workspace &&
        result.anchor.record_id === id &&
        result.anchor.action === actions[checkedKind],
    );
    return result;
  }
}
