/** Strictly bound current lifecycle and history projections. */
import {
  choice,
  integer,
  list,
  object,
  requireContract,
  timestamp,
  uuid,
} from "./persona-validation";
import {
  requirements,
  parseLifecycleReceipt,
  type RequirementStatus,
  type ConcernStatus,
  type LifecycleReceipt,
  type LifecycleProfile,
  type LifecyclePage,
} from "./persona-lifecycle-contracts";

function parseRequirement(raw: unknown): RequirementStatus {
  const r = object(raw, ["requirement", "status", "assessment"]);
  const result = {
    requirement: choice(r.requirement, requirements),
    status: choice(r.status, [
      "missing",
      "approved",
      "changes_requested",
      "withdrawn",
      "expired",
      "unavailable",
    ]),
    assessment:
      r.assessment === null ? null : parseLifecycleReceipt(r.assessment),
  };
  requireContract(
    (result.status === "missing") === (result.assessment === null),
  );
  if (result.assessment) {
    requireContract(
      result.assessment.content.kind === "assessment" &&
        result.assessment.content.requirement === result.requirement,
    );
    const content = result.assessment.content;
    if (content.kind === "assessment")
      requireContract(
        content.decision === "approved"
          ? ["approved", "expired", "unavailable"].includes(result.status)
          : result.status === content.decision,
      );
  }
  return result;
}
function parseConcern(raw: unknown): ConcernStatus {
  const r = object(raw, ["report", "response"]);
  const result = {
    report: parseLifecycleReceipt(r.report),
    response: r.response === null ? null : parseLifecycleReceipt(r.response),
  };
  requireContract(result.report.content.kind === "concern");
  if (result.response)
    requireContract(
      result.response.content.kind === "response" &&
        result.response.content.concern_id === result.report.id &&
        result.response.persona_id === result.report.persona_id &&
        result.response.workspace_id === result.report.workspace_id,
    );
  return result;
}
export function parseLifecycleProfile(raw: unknown): LifecycleProfile {
  const r = object(raw, [
    "workspace_id",
    "persona_id",
    "version_id",
    "dossier",
    "requirements",
    "concerns",
    "suspended",
    "evaluated_at",
  ]);
  requireContract(typeof r.suspended === "boolean");
  const profile = {
    workspace_id: uuid(r.workspace_id),
    persona_id: uuid(r.persona_id),
    version_id: uuid(r.version_id),
    dossier: r.dossier === null ? null : parseLifecycleReceipt(r.dossier),
    requirements: list(r.requirements, parseRequirement, 3, 3),
    concerns: list(r.concerns, parseConcern, 20),
    suspended: r.suspended,
    evaluated_at: timestamp(r.evaluated_at),
  };
  requireContract(
    new Set(profile.requirements.map((v) => v.requirement)).size === 3,
  );
  validateProfileBindings(profile);
  return profile;
}
function validateProfileBindings(profile: LifecycleProfile): void {
  const bound = (v: LifecycleReceipt) =>
    v.workspace_id === profile.workspace_id &&
    v.persona_id === profile.persona_id;
  if (profile.dossier)
    requireContract(
      bound(profile.dossier) &&
        profile.dossier.version_id === profile.version_id &&
        profile.dossier.content.kind === "dossier",
    );
  profile.requirements.forEach((v) => {
    if (v.assessment)
      requireContract(
        bound(v.assessment) &&
          v.assessment.version_id === profile.version_id &&
          v.assessment.content.kind === "assessment" &&
          v.assessment.content.profile_id === profile.dossier?.id,
      );
    if (v.status === "approved" && v.assessment?.content.kind === "assessment")
      requireContract(
        Date.parse(v.assessment.content.valid_until) >
          Date.parse(profile.evaluated_at),
      );
    if (v.status === "expired" && v.assessment?.content.kind === "assessment")
      requireContract(
        Date.parse(v.assessment.content.valid_until) <=
          Date.parse(profile.evaluated_at),
      );
  });
  profile.concerns.forEach((v) =>
    requireContract(bound(v.report) && (!v.response || bound(v.response))),
  );
  requireContract(
    new Set(profile.concerns.map((v) => v.report.id)).size ===
      profile.concerns.length,
  );
  requireContract(
    profile.suspended ||
      !profile.concerns.some(
        (v) =>
          v.response?.content.kind === "response" &&
          v.response.content.decision === "suspended",
      ),
  );
}
export function parseLifecyclePage(raw: unknown): LifecyclePage {
  const r = object(raw, [
    "workspace_id",
    "version_id",
    "items",
    "next_before_ordinal",
    "concerns",
  ]);
  const page = {
    workspace_id: uuid(r.workspace_id),
    version_id: uuid(r.version_id),
    items: list(r.items, parseLifecycleReceipt, 20),
    next_before_ordinal:
      r.next_before_ordinal === null ? null : integer(r.next_before_ordinal),
    concerns: list(r.concerns, parseConcern, 20),
  };
  requireContract(
    page.items.every(
      (v, i) =>
        v.workspace_id === page.workspace_id &&
        (i === 0 || v.ordinal < page.items[i - 1].ordinal),
    ),
  );
  requireContract(
    page.next_before_ordinal === null ||
      page.next_before_ordinal === page.items.at(-1)?.ordinal,
  );
  requireContract(
    new Set(page.concerns.map((v) => v.report.id)).size ===
      page.concerns.length &&
      page.concerns.length ===
        page.items.filter((v) => v.content.kind === "concern").length &&
      page.concerns.every((v) =>
        page.items.some(
          (item) =>
            item.id === v.report.id &&
            JSON.stringify(item) === JSON.stringify(v.report),
        ),
      ),
  );
  return page;
}
