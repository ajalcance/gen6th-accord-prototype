/** Attributed workspace declarations; approvals are scoped human assessments. */
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

export const requirements = ["operator", "rights", "content"] as const;
export type Requirement = (typeof requirements)[number];
export const rightKinds = [
  "likeness",
  "voice",
  "source_performance",
  "artwork",
  "other",
] as const;
export type Right = {
  kind: (typeof rightKinds)[number];
  holder: string;
  scope: string;
  withdrawal: string;
  evidence_id: string;
  starts_at: string;
  ends_at: string;
};
export type Dossier = {
  kind: "dossier";
  operator: {
    name: string;
    actor_ref: string;
    organization: string | null;
    authority: string;
    evidence_id: string;
  };
  rights: Right[];
  provenance: {
    method: "generated" | "human_driven" | "mixed";
    provider: string;
    model_version: string;
    disclosure: string;
    source: "creator_declared";
  };
};
export type Assessment = {
  kind: "assessment";
  profile_id: string;
  requirement: Requirement;
  decision: "approved" | "changes_requested" | "withdrawn";
  statement: string;
  valid_until: string;
};
export type Concern = {
  kind: "concern";
  category: "rights" | "identity" | "content" | "safety" | "other";
  statement: string;
};
export type Response = {
  kind: "response";
  concern_id: string;
  decision: "open" | "suspended" | "resolved";
  statement: string;
};
export type LifecycleContent = Dossier | Assessment | Concern | Response;
export type AppendLifecycle = {
  version_id: string;
  request_id: string;
  expected_previous_id: string | null;
  content: LifecycleContent;
};
export type LifecycleReceipt = AppendLifecycle & {
  id: string;
  workspace_id: string;
  persona_id: string;
  ordinal: number;
  actor_ref: string;
  recorded_at: string;
  evidence_digests: Record<string, string>;
};
export type RequirementStatus = {
  requirement: Requirement;
  status:
    | "missing"
    | "approved"
    | "changes_requested"
    | "withdrawn"
    | "expired"
    | "unavailable";
  assessment: LifecycleReceipt | null;
};
export type ConcernStatus = {
  report: LifecycleReceipt;
  response: LifecycleReceipt | null;
};
export type LifecycleProfile = {
  workspace_id: string;
  persona_id: string;
  version_id: string;
  dossier: LifecycleReceipt | null;
  requirements: RequirementStatus[];
  concerns: ConcernStatus[];
  suspended: boolean;
  evaluated_at: string;
};
export type LifecyclePage = {
  workspace_id: string;
  version_id: string;
  items: LifecycleReceipt[];
  next_before_ordinal: number | null;
  concerns: ConcernStatus[];
};

export function parseRight(raw: unknown): Right {
  const r = object(raw, [
    "kind",
    "holder",
    "scope",
    "withdrawal",
    "evidence_id",
    "starts_at",
    "ends_at",
  ]);
  const value = {
    kind: choice(r.kind, rightKinds),
    holder: text(r.holder, 80),
    scope: text(r.scope, 500),
    withdrawal: text(r.withdrawal, 500),
    evidence_id: uuid(r.evidence_id),
    starts_at: timestamp(r.starts_at),
    ends_at: timestamp(r.ends_at),
  };
  requireContract(Date.parse(value.ends_at) > Date.parse(value.starts_at));
  return value;
}
export function parseDossier(raw: unknown): Dossier {
  const r = object(raw, ["kind", "operator", "rights", "provenance"]),
    o = object(r.operator, [
      "name",
      "actor_ref",
      "organization",
      "authority",
      "evidence_id",
    ]),
    p = object(r.provenance, [
      "method",
      "provider",
      "model_version",
      "disclosure",
      "source",
    ]);
  return {
    kind: choice(r.kind, ["dossier"]),
    operator: {
      name: text(o.name, 80),
      actor_ref: text(o.actor_ref, 64),
      organization: o.organization === null ? null : text(o.organization, 80),
      authority: text(o.authority, 500),
      evidence_id: uuid(o.evidence_id),
    },
    rights: list(r.rights, parseRight, 8, 1),
    provenance: {
      method: choice(p.method, ["generated", "human_driven", "mixed"]),
      provider: text(p.provider, 80),
      model_version: text(p.model_version, 80),
      disclosure: text(p.disclosure, 500),
      source: choice(p.source, ["creator_declared"]),
    },
  };
}
export function parseLifecycleContent(raw: unknown): LifecycleContent {
  requireContract(raw !== null && typeof raw === "object" && "kind" in raw);
  const kind = (raw as { kind: unknown }).kind;
  if (kind === "dossier") return parseDossier(raw);
  if (kind === "assessment") {
    const r = object(raw, [
      "kind",
      "profile_id",
      "requirement",
      "decision",
      "statement",
      "valid_until",
    ]);
    return {
      kind,
      profile_id: uuid(r.profile_id),
      requirement: choice(r.requirement, requirements),
      decision: choice(r.decision, [
        "approved",
        "changes_requested",
        "withdrawn",
      ]),
      statement: text(r.statement, 500),
      valid_until: timestamp(r.valid_until),
    };
  }
  if (kind === "concern") {
    const r = object(raw, ["kind", "category", "statement"]);
    return {
      kind,
      category: choice(r.category, [
        "rights",
        "identity",
        "content",
        "safety",
        "other",
      ]),
      statement: text(r.statement, 500),
    };
  }
  const r = object(raw, ["kind", "concern_id", "decision", "statement"]);
  return {
    kind: choice(r.kind, ["response"]),
    concern_id: uuid(r.concern_id),
    decision: choice(r.decision, ["open", "suspended", "resolved"]),
    statement: text(r.statement, 500),
  };
}
export function parseAppendLifecycle(raw: unknown): AppendLifecycle {
  const r = object(raw, [
    "version_id",
    "request_id",
    "expected_previous_id",
    "content",
  ]);
  const command = {
    version_id: uuid(r.version_id),
    request_id: uuid(r.request_id),
    expected_previous_id:
      r.expected_previous_id === null ? null : uuid(r.expected_previous_id),
    content: parseLifecycleContent(r.content),
  };
  requireContract(
    new TextEncoder().encode(JSON.stringify(command)).length <= 12288,
  );
  return command;
}
export function parseLifecycleReceipt(raw: unknown): LifecycleReceipt {
  const r = object(raw, [
    "version_id",
    "request_id",
    "expected_previous_id",
    "content",
    "id",
    "workspace_id",
    "persona_id",
    "ordinal",
    "actor_ref",
    "recorded_at",
    "evidence_digests",
  ]);
  requireContract(
    r.evidence_digests !== null &&
      typeof r.evidence_digests === "object" &&
      !Array.isArray(r.evidence_digests),
  );
  const digests: Record<string, string> = {};
  const entries = Object.entries(r.evidence_digests as Record<string, unknown>);
  requireContract(entries.length <= 9);
  entries.forEach(([key, value]) => {
    digests[uuid(key)] = hex(value, 64);
  });
  return {
    ...parseAppendLifecycle({
      version_id: r.version_id,
      request_id: r.request_id,
      expected_previous_id: r.expected_previous_id,
      content: r.content,
    }),
    id: uuid(r.id),
    workspace_id: uuid(r.workspace_id),
    persona_id: uuid(r.persona_id),
    ordinal: integer(r.ordinal),
    actor_ref: text(r.actor_ref, 64),
    recorded_at: timestamp(r.recorded_at),
    evidence_digests: digests,
  };
}
