/** Explicit production roles and submitted references; no legal rights verdict. */
import {
  choice,
  list,
  object,
  requireContract,
  text,
  uuid,
} from "./persona-validation";

export type ProductionUse = {
  title: string;
  episode: string;
  role_name: string;
  adaptation: string;
  supporting_references: { kind: "consent" | "claim"; evidence_id: string }[];
  governance_profile_id?: string;
  responsible_operator?: string;
  use_mode?: "production" | "trial";
  distribution?: "private" | "public";
  voice_use?: boolean;
};
export function parseProduction(value: unknown): ProductionUse {
  const bound =
    value !== null &&
    typeof value === "object" &&
    Object.hasOwn(value, "governance_profile_id");
  const row = object(value, [
    "title",
    "episode",
    "role_name",
    "adaptation",
    "supporting_references",
    ...(bound
      ? [
          "governance_profile_id",
          "responsible_operator",
          "use_mode",
          "distribution",
          "voice_use",
        ]
      : []),
  ]);
  const references = list(
    row.supporting_references,
    (value) => {
      const item = object(value, ["kind", "evidence_id"]);
      return {
        kind: choice(item.kind, ["consent", "claim"]),
        evidence_id: uuid(item.evidence_id),
      };
    },
    8,
  );
  requireContract(
    new Set(references.map((item) => item.evidence_id)).size ===
      references.length,
  );
  const lifecycle = bound
    ? {
        governance_profile_id: uuid(row.governance_profile_id),
        responsible_operator: text(row.responsible_operator, 64),
        use_mode: choice(row.use_mode, ["production", "trial"]),
        distribution: choice(row.distribution, ["private", "public"]),
        voice_use: row.voice_use as boolean,
      }
    : {};
  if (bound) {
    requireContract(typeof row.voice_use === "boolean");
    requireContract(row.use_mode !== "trial" || row.distribution === "private");
  }
  return {
    title: text(row.title, 80),
    episode: text(row.episode, 80),
    role_name: text(row.role_name, 80),
    adaptation: text(row.adaptation, 500),
    supporting_references: references,
    ...lifecycle,
  };
}
export function productionDraft(
  fields: Record<string, string>,
): ProductionUse | undefined {
  if (fields.production !== "yes") return undefined;
  return parseProduction({
    title: fields.productionTitle,
    episode: fields.episode,
    role_name: fields.roleName,
    adaptation: fields.adaptation,
    supporting_references: (fields.references ?? "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => {
        const [kind, evidence_id, extra] = item.split(":");
        requireContract(extra === undefined);
        return { kind, evidence_id };
      }),
    ...(fields.lifecycle === "yes"
      ? {
          governance_profile_id: fields.lifecycleProfile,
          responsible_operator: fields.lifecycleOperator,
          use_mode: fields.useMode || "production",
          distribution: fields.distribution || "public",
          voice_use: fields.voiceUse === "yes",
        }
      : {}),
  });
}
