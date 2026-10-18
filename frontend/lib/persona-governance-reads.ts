import type { PersonaOperation, PersonaTransport } from "./persona-gateway";
import { uuid } from "./persona-validation";
import {
  campaignPage,
  evidencePage,
  objectQuery,
  versionPage,
  versionQuery,
  type ObjectQuery,
  type VersionHistoryQuery,
} from "./persona-governance-pages";

export class PersonaGovernanceReads {
  constructor(
    private readonly workspace: string,
    private readonly transport: PersonaTransport,
  ) {}
  private async receive(
    operation: PersonaOperation,
    command: unknown,
    signal?: AbortSignal,
  ) {
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    const raw = await this.transport(
      operation,
      this.workspace,
      command,
      signal,
    );
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    return raw;
  }
  async versions(
    personaId: string,
    value: VersionHistoryQuery,
    signal?: AbortSignal,
  ) {
    const id = uuid(personaId),
      query = versionQuery(value);
    const raw = await this.receive(
      "versionHistory",
      { persona_id: id, ...query },
      signal,
    );
    return versionPage(raw, this.workspace, id, query);
  }
  async campaigns(versionId: string, value: ObjectQuery, signal?: AbortSignal) {
    const id = uuid(versionId),
      query = objectQuery(value);
    const raw = await this.receive(
      "campaignOffers",
      { version_id: id, ...query },
      signal,
    );
    return campaignPage(raw, this.workspace, id, query);
  }
  async evidence(versionId: string, value: ObjectQuery, signal?: AbortSignal) {
    const id = uuid(versionId),
      query = objectQuery(value);
    const raw = await this.receive(
      "evidenceList",
      { version_id: id, ...query },
      signal,
    );
    return evidencePage(raw, this.workspace, id, query);
  }
}
