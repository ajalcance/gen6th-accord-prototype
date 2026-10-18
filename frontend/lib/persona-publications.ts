import { apiClient } from "./api-client";
import {
  parsePackage,
  type SignedPassport,
} from "./persona-passport-contracts";
import {
  choice,
  integer,
  object,
  requireContract,
  text,
  timestamp,
  uuid,
} from "./persona-validation";

export const publicFields = [
  "name",
  "biography",
  "human_contribution",
  "ai_disclosure",
  "production_name",
  "purpose",
  "conditions",
  "portrait_sha256",
] as const;
export type PublicField = (typeof publicFields)[number];
export type ApprovalCommand = {
  request_id: string;
  campaign_id: string;
  fields: PublicField[];
};
export type PublicationReceipt = {
  workspace_id: string;
  publication_id: string;
  path: string;
  package: SignedPassport;
};
export type PublicValues = Partial<Record<PublicField, string>> & {
  name: string;
  ai_disclosure: string;
};
export function publicProjection(packet: SignedPassport) {
  const row = object(packet.payload, [
    "format",
    "publication_id",
    "approved_at",
    "valid_from",
    "valid_until",
    "version_revision",
    "values",
    "claims",
  ]);
  requireContract(
    row.format === "accord-public-passport-v1" &&
      row.claims === "creator_statements_not_independently_verified",
  );
  requireContract(
    row.values !== null &&
      typeof row.values === "object" &&
      !Array.isArray(row.values),
  );
  const values: Partial<Record<PublicField, string>> = {};
  for (const [key, value] of Object.entries(row.values))
    values[choice(key, publicFields)] = text(value, 500);
  requireContract(values.name && values.ai_disclosure);
  if (values.portrait_sha256)
    requireContract(/^[0-9a-f]{64}$/.test(values.portrait_sha256));
  const from = timestamp(row.valid_from),
    until = timestamp(row.valid_until);
  requireContract(Date.parse(until) > Date.parse(from));
  return {
    id: uuid(row.publication_id),
    approved: timestamp(row.approved_at),
    from,
    until,
    revision: integer(row.version_revision),
    values: values as PublicValues,
  };
}
export function parsePublication(
  raw: unknown,
  workspace: string,
): PublicationReceipt {
  const row = object(raw, [
    "workspace_id",
    "publication_id",
    "path",
    "package",
  ]);
  const id = uuid(row.publication_id),
    packet = parsePackage(row.package);
  requireContract(
    uuid(row.workspace_id) === workspace &&
      row.path === `/p/${workspace}/${id}` &&
      publicProjection(packet).id === id,
  );
  return {
    workspace_id: workspace,
    publication_id: id,
    path: row.path,
    package: packet,
  };
}
export type PublicationGateway = {
  workspaceId: string;
  history(
    campaign: string,
    after: string | null,
    signal: AbortSignal,
  ): Promise<{
    items: { receipt: PublicationReceipt; withdrawn: boolean }[];
    next: string | null;
  }>;
  approve(
    command: ApprovalCommand,
    signal: AbortSignal,
  ): Promise<PublicationReceipt>;
  unpublish(id: string, signal: AbortSignal): Promise<PublicationReceipt>;
};
export function publicationGateway(workspace: string): PublicationGateway {
  const workspaceId = uuid(workspace);
  async function post(route: string, body: unknown, signal: AbortSignal) {
    const raw = await apiClient.post(
      `/api/workspaces/${workspaceId}/personas/publications/${route}`,
      body,
      {
        signal,
        credentials: "same-origin",
        mode: "same-origin",
        cache: "no-store",
        redirect: "error",
        retries: 0,
        timeoutMs: 90000,
      },
    );
    requireContract(!signal.aborted);
    return parsePublication(raw, workspaceId);
  }
  return {
    workspaceId,
    async history(campaign, after, signal) {
      const data = object(
        await apiClient.post(
          `/api/workspaces/${workspaceId}/personas/publications/history`,
          {
            campaign_id: uuid(campaign),
            after_id: after === null ? null : uuid(after),
          },
          {
            signal,
            credentials: "same-origin",
            mode: "same-origin",
            cache: "no-store",
            redirect: "error",
            retries: 0,
          },
        ),
        ["workspace_id", "campaign_id", "items", "next_after_id"],
      );
      requireContract(
        data.workspace_id === workspaceId &&
          data.campaign_id === campaign &&
          Array.isArray(data.items) &&
          data.items.length <= 20 &&
          !signal.aborted,
      );
      const items = data.items.map((value) => {
        const item = object(value, ["receipt", "withdrawn"]);
        requireContract(typeof item.withdrawn === "boolean");
        return {
          receipt: parsePublication(item.receipt, workspaceId),
          withdrawn: item.withdrawn,
        };
      });
      requireContract(
        new Set(items.map((i) => i.receipt.publication_id)).size ===
          items.length,
      );
      const next =
        data.next_after_id === null ? null : uuid(data.next_after_id);
      requireContract(
        next === null ||
          (items.length === 20 && next === items[19].receipt.publication_id),
      );
      return { items, next };
    },
    async approve(command, signal) {
      const result = await post(
        "approve",
        {
          ...command,
          request_id: uuid(command.request_id),
          campaign_id: uuid(command.campaign_id),
        },
        signal,
      );
      requireContract(
        Object.keys(publicProjection(result.package).values).sort().join() ===
          [...command.fields].sort().join(),
      );
      return result;
    },
    async unpublish(id, signal) {
      const result = await post(
        "unpublish",
        { publication_id: uuid(id) },
        signal,
      );
      requireContract(result.publication_id === id);
      return result;
    },
  };
}
export function parsePublicPage(raw: unknown, publication: string) {
  const row = object(raw, ["package", "verification"]),
    packet = parsePackage(row.package),
    projection = publicProjection(packet);
  requireContract(projection.id === publication);
  const verification = object(row.verification, [
    "integrity",
    "current_use",
    "evaluated_at",
  ]);
  const integrity = choice(verification.integrity, [
    "valid",
    "invalid_signature",
    "untrusted_key",
    "invalid_package",
    "binding_mismatch",
  ]);
  const currentUse = choice(verification.current_use, [
    "eligible",
    "blocked",
    "unavailable",
  ]);
  requireContract(integrity === "valid" || currentUse === "unavailable");
  return {
    packet,
    projection,
    integrity,
    currentUse,
    evaluated: timestamp(verification.evaluated_at),
  };
}
