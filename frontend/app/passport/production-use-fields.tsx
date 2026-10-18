import type { CampaignScope } from "../../lib/persona-contracts";
import { productionDraft } from "../../lib/persona-production";
import ProductionReferences from "./production-references";
import LifecycleUse from "./lifecycle-use";
import type { SavedPersonaSource } from "./saved-source";
import {
  TextFields,
  type TextFieldSpec,
  type WriteDraftState,
} from "./prepared-write-common";

const specs: TextFieldSpec[] = [
  {
    field: "productionTitle",
    label: "Production title",
    placeholder: "Name the film, series or production.",
    max: 80,
    multiline: false,
  },
  {
    field: "episode",
    label: "Episode or named installment",
    placeholder: "For example, Episode 1 or Pilot.",
    max: 80,
    multiline: false,
  },
  {
    field: "roleName",
    label: "Character or role name",
    placeholder: "Name this performer's role.",
    max: 80,
    multiline: false,
  },
  {
    field: "adaptation",
    label: "Permitted appearance and adaptation",
    placeholder: "Describe allowed changes, such as costume or styling.",
  },
];
export function productionReady(fields: Record<string, string>): boolean {
  try {
    productionDraft(fields);
    return true;
  } catch {
    return false;
  }
}
export function ProductionUseFields({
  draft,
  source,
  versionId,
}: {
  draft: WriteDraftState;
  source: SavedPersonaSource;
  versionId: string;
}) {
  return (
    <fieldset>
      <legend>Production use</legend>
      <label className="prepared-confirm">
        <input
          type="checkbox"
          checked={draft.fields.production === "yes"}
          onChange={(event) =>
            draft.change("production", event.target.checked ? "yes" : "")
          }
        />
        Name a production and role
      </label>
      {draft.fields.production === "yes" && (
        <>
          <p>
            The saved persona is the continuing performer. This role and episode
            apply only to this offer.
          </p>
          <TextFields specs={specs} draft={draft} />
          <ProductionReferences
            source={source}
            versionId={versionId}
            draft={draft}
          />
          <LifecycleUse source={source} versionId={versionId} draft={draft} />
          <p className="help">
            References are optional submitted consent or ownership claims. Use
            evidence from this exact version. A clean scan does not verify
            rights. Unavailable or expired referenced evidence blocks use.
          </p>
        </>
      )}
    </fieldset>
  );
}
export function SavedProductionUse({ scope }: { scope: CampaignScope }) {
  const production = scope.production;
  if (!production) return null;
  return (
    <section aria-label="Named production use">
      <h4>
        {production.title} · {production.episode}
      </h4>
      <p>Role: {production.role_name}</p>
      <p>Adaptation: {production.adaptation}</p>
      {production.governance_profile_id && (
        <p>
          Mode: {production.use_mode} · {production.distribution} distribution ·
          operator {production.responsible_operator} ·{" "}
          {production.voice_use ? "Voice use included" : "Voice use excluded"}
        </p>
      )}
      <p className="help">
        The performer identity remains attached to the exact saved version.
        References are submitted claims; rights have not been independently
        verified.
      </p>
      {production.supporting_references.length ? (
        <ul>
          {production.supporting_references.map((item) => (
            <li key={item.evidence_id}>
              {item.kind}: {item.evidence_id}
            </li>
          ))}
        </ul>
      ) : (
        <p>No supporting consent or claim references attached.</p>
      )}
    </section>
  );
}
