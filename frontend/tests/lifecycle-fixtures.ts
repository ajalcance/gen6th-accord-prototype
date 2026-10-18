import type {
  Assessment,
  Dossier,
  LifecycleProfile,
  LifecycleReceipt,
  Requirement,
} from "../lib/persona-lifecycle-contracts";
import { version } from "./prepared-write-fixtures";

export const id = (value: number) =>
  `00000000-0000-4000-8000-${String(value).padStart(12, "0")}`;
export const lifecycleDossier: Dossier = {
  kind: "dossier",
  operator: {
    name: "Fictional operator",
    actor_ref: "operator",
    organization: "Fixture studio",
    authority: "Declared studio management",
    evidence_id: id(301),
  },
  rights: [
    {
      kind: "likeness",
      holder: "Fixture studio",
      scope: "Private rehearsal",
      withdrawal: "Owner may withdraw",
      evidence_id: id(302),
      starts_at: "2026-01-01T00:00:00Z",
      ends_at: "2027-01-01T00:00:00Z",
    },
  ],
  provenance: {
    method: "mixed",
    provider: "Fixture tools",
    model_version: "One",
    disclosure: "Synthetic fixture",
    source: "creator_declared",
  },
};
export const lifecycleReceipt: LifecycleReceipt = {
  id: id(303),
  workspace_id: version.workspace_id,
  persona_id: version.persona_id,
  version_id: version.version_id,
  request_id: id(304),
  expected_previous_id: null,
  ordinal: 1,
  actor_ref: version.creator_ref,
  recorded_at: version.recorded_at,
  content: lifecycleDossier,
  evidence_digests: { [id(301)]: "a".repeat(64), [id(302)]: "b".repeat(64) },
};
export function review(requirement: Requirement, n: number): LifecycleReceipt {
  const content: Assessment = {
    kind: "assessment",
    profile_id: lifecycleReceipt.id,
    requirement,
    decision: "approved",
    statement: "Synthetic independent assessment",
    valid_until: "2027-01-01T00:00:00Z",
  };
  return {
    ...lifecycleReceipt,
    id: id(310 + n),
    request_id: id(320 + n),
    ordinal: n + 2,
    actor_ref: "reviewer",
    content,
    evidence_digests: {},
  };
}
export const lifecycleProfile: LifecycleProfile = {
  workspace_id: version.workspace_id,
  persona_id: version.persona_id,
  version_id: version.version_id,
  dossier: lifecycleReceipt,
  requirements: ["operator", "rights", "content"].map((requirement, i) => ({
    requirement: requirement as Requirement,
    status: "approved",
    assessment: review(requirement as Requirement, i),
  })),
  concerns: [],
  suspended: false,
  evaluated_at: version.recorded_at,
};
