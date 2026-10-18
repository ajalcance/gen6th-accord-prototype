/** Private attributed annotations; parsed receipts never imply ownership or publication. */
import { apiClient } from "./api-client";
import {
  choice,
  integer,
  list,
  object,
  requireContract,
  text,
  timestamp,
  uuid,
} from "./persona-validation";

export const creditRoles = [
  "design",
  "writing",
  "direction",
  "illustration",
  "source_performance",
  "other",
] as const;
export type Credit = {
  name: string;
  kind: "human" | "organization";
  role: (typeof creditRoles)[number];
  actor_ref: string | null;
  evidence_id: string | null;
};
export type CreditContent = { aliases: string[]; credits: Credit[] };
export type SaveCredits = {
  request_id: string;
  version_id: string;
  expected_previous_id: string | null;
  content: CreditContent;
};
export type CreditSnapshot = {
  id: string;
  workspace_id: string;
  version_id: string;
  request_id: string;
  ordinal: number;
  declared_by: string;
  recorded_at: string;
  content: CreditContent;
};
export type ConfirmCredit = {
  request_id: string;
  version_id: string;
  profile_id: string;
  credit_index: number;
};
export type CreditConfirmation = ConfirmCredit & {
  id: string;
  workspace_id: string;
  actor_ref: string;
  recorded_at: string;
};
export type CreditProfile = {
  workspace_id: string;
  version_id: string;
  snapshot: CreditSnapshot | null;
  confirmations: CreditConfirmation[];
};

function parseCredit(raw: unknown): Credit {
  const r = object(raw, ["name", "kind", "role", "actor_ref", "evidence_id"]);
  const c = {
    name: text(r.name, 80),
    kind: choice(r.kind, ["human", "organization"]),
    role: choice(r.role, creditRoles),
    actor_ref: r.actor_ref === null ? null : text(r.actor_ref, 64),
    evidence_id: r.evidence_id === null ? null : uuid(r.evidence_id),
  };
  requireContract(c.kind === "human" || c.actor_ref === null);
  return c;
}
export function parseCreditContent(raw: unknown): CreditContent {
  const r = object(raw, ["aliases", "credits"]);
  const content = {
    aliases: list(r.aliases, (v) => text(v, 80), 8),
    credits: list(r.credits, parseCredit, 12),
  };
  requireContract(
    new Set(content.aliases.map((v) => v.toLowerCase())).size ===
      content.aliases.length,
  );
  requireContract(
    new Set(content.credits.map((v) => JSON.stringify(v))).size ===
      content.credits.length,
  );
  requireContract(
    new TextEncoder().encode(JSON.stringify(content)).length <= 10000,
  );
  return content;
}
export function parseSaveCredits(raw: unknown): SaveCredits {
  const r = object(raw, [
    "request_id",
    "version_id",
    "expected_previous_id",
    "content",
  ]);
  return {
    request_id: uuid(r.request_id),
    version_id: uuid(r.version_id),
    expected_previous_id:
      r.expected_previous_id === null ? null : uuid(r.expected_previous_id),
    content: parseCreditContent(r.content),
  };
}
export function parseConfirmCredit(raw: unknown): ConfirmCredit {
  const r = object(raw, [
    "request_id",
    "version_id",
    "profile_id",
    "credit_index",
  ]);
  const result = {
    request_id: uuid(r.request_id),
    version_id: uuid(r.version_id),
    profile_id: uuid(r.profile_id),
    credit_index: integer(r.credit_index, 0),
  };
  requireContract(result.credit_index <= 11);
  return result;
}
export function parseCreditSnapshot(raw: unknown): CreditSnapshot {
  const r = object(raw, [
    "id",
    "workspace_id",
    "version_id",
    "request_id",
    "ordinal",
    "declared_by",
    "recorded_at",
    "content",
  ]);
  return {
    id: uuid(r.id),
    workspace_id: uuid(r.workspace_id),
    version_id: uuid(r.version_id),
    request_id: uuid(r.request_id),
    ordinal: integer(r.ordinal),
    declared_by: text(r.declared_by, 64),
    recorded_at: timestamp(r.recorded_at),
    content: parseCreditContent(r.content),
  };
}
export function parseCreditConfirmation(raw: unknown): CreditConfirmation {
  const r = object(raw, [
    "id",
    "workspace_id",
    "version_id",
    "request_id",
    "profile_id",
    "credit_index",
    "actor_ref",
    "recorded_at",
  ]);
  return {
    ...parseConfirmCredit({
      request_id: r.request_id,
      version_id: r.version_id,
      profile_id: r.profile_id,
      credit_index: r.credit_index,
    }),
    id: uuid(r.id),
    workspace_id: uuid(r.workspace_id),
    actor_ref: text(r.actor_ref, 64),
    recorded_at: timestamp(r.recorded_at),
  };
}
export function parseCreditProfile(raw: unknown): CreditProfile {
  const r = object(raw, [
    "workspace_id",
    "version_id",
    "snapshot",
    "confirmations",
  ]);
  const p = {
    workspace_id: uuid(r.workspace_id),
    version_id: uuid(r.version_id),
    snapshot: r.snapshot === null ? null : parseCreditSnapshot(r.snapshot),
    confirmations: list(r.confirmations, parseCreditConfirmation, 12),
  };
  if (!p.snapshot) requireContract(p.confirmations.length === 0);
  else validateProfile(p, p.snapshot);
  return p;
}
function validateProfile(p: CreditProfile, s: CreditSnapshot) {
  requireContract(
    s.workspace_id === p.workspace_id && s.version_id === p.version_id,
  );
  requireContract(
    new Set(p.confirmations.map((c) => c.credit_index)).size ===
      p.confirmations.length,
  );
  p.confirmations.forEach((c) => {
    const credit = s.content.credits[c.credit_index];
    requireContract(
      c.workspace_id === p.workspace_id &&
        c.version_id === p.version_id &&
        c.profile_id === s.id &&
        credit?.kind === "human" &&
        credit.actor_ref === c.actor_ref,
    );
  });
}
export type CreditTransport = (
  path: string,
  body: unknown,
  signal: AbortSignal,
) => Promise<unknown>;
function creditPost(
  workspace: string,
  transport?: CreditTransport,
): CreditTransport {
  return async (path: string, body: unknown, signal: AbortSignal) => {
    if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
    const result = await (transport
      ? transport(path, body, signal)
      : apiClient.post(
          `/api/workspaces/${workspace}/personas/credits/${path}`,
          body,
          {
            signal,
            credentials: "same-origin",
            cache: "no-store",
            mode: "same-origin",
            redirect: "error",
            retries: 0,
          },
        ));
    if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
    return result;
  };
}
export function creditGateway(
  workspaceId: string,
  transport?: CreditTransport,
) {
  const workspace = uuid(workspaceId),
    post = creditPost(workspace, transport);
  return {
    workspaceId: workspace,
    async read(version: string, signal: AbortSignal) {
      const id = uuid(version),
        p = parseCreditProfile(await post("read", { version_id: id }, signal));
      requireContract(p.workspace_id === workspace && p.version_id === id);
      return p;
    },
    async save(command: SaveCredits, signal: AbortSignal) {
      const body = parseSaveCredits(command),
        r = parseCreditSnapshot(await post("save", body, signal));
      requireContract(
        r.workspace_id === workspace &&
          r.version_id === body.version_id &&
          r.request_id === body.request_id &&
          r.id !== body.expected_previous_id &&
          JSON.stringify(r.content) === JSON.stringify(body.content),
      );
      requireContract(body.expected_previous_id !== null || r.ordinal === 1);
      return r;
    },
    async confirm(command: ConfirmCredit, signal: AbortSignal) {
      const body = parseConfirmCredit(command),
        r = parseCreditConfirmation(await post("confirm", body, signal));
      requireContract(
        r.workspace_id === workspace &&
          r.version_id === body.version_id &&
          r.profile_id === body.profile_id &&
          r.credit_index === body.credit_index &&
          r.request_id === body.request_id,
      );
      return r;
    },
  };
}
export type CreditGateway = ReturnType<typeof creditGateway>;
