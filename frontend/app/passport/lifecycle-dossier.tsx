import {
  parseDossier,
  rightKinds,
  type Dossier,
} from "../../lib/persona-lifecycle-contracts";
import LifecycleForm, { type LifecycleFormProps } from "./lifecycle-form";
import {
  TextFields,
  type WriteDraftState,
  type TextFieldSpec,
} from "./prepared-write-common";
import CreditEvidencePicker from "./credit-evidence-picker";

const spec = (field: string, label: string, max = 500): TextFieldSpec => ({
  field,
  label,
  max,
  multiline: max === 500,
  placeholder: label,
});
const operatorFields = [
  spec("operatorName", "Responsible operator name", 80),
  spec("operatorAccount", "Operator workspace account reference", 64),
  spec("authority", "Describe the operator's authority"),
];
const provenanceFields = [
  spec("provider", "Creation provider or tools", 80),
  spec("model", "Model/tool version or not applicable", 80),
  spec("disclosure", "Describe AI use and human involvement"),
];

function dossierDraft(fields: Record<string, string>): Dossier {
  return parseDossier({
    kind: "dossier",
    operator: {
      name: fields.operatorName,
      actor_ref: fields.operatorAccount,
      organization: fields.organization?.trim() || null,
      authority: fields.authority,
      evidence_id: fields.operatorEvidence,
    },
    rights: Array.from({ length: Number(fields.rightCount || 1) }, (_, i) => ({
      kind: fields[`right${i}Kind`] || "likeness",
      holder: fields[`right${i}Holder`],
      scope: fields[`right${i}Scope`],
      withdrawal: fields[`right${i}Withdrawal`],
      evidence_id: fields[`right${i}Evidence`],
      starts_at: fields[`right${i}Starts`],
      ends_at: fields[`right${i}Ends`],
    })),
    provenance: {
      method: fields.method || "mixed",
      provider: fields.provider,
      model_version: fields.model,
      disclosure: fields.disclosure,
      source: "creator_declared",
    },
  });
}
function initialFields(dossier: Dossier | null): Record<string, string> {
  if (!dossier) return { rightCount: "1", method: "mixed" };
  const fields: Record<string, string> = {
    operatorName: dossier.operator.name,
    operatorAccount: dossier.operator.actor_ref,
    organization: dossier.operator.organization || "",
    authority: dossier.operator.authority,
    operatorEvidence: dossier.operator.evidence_id,
    rightCount: String(dossier.rights.length),
    method: dossier.provenance.method,
    provider: dossier.provenance.provider,
    model: dossier.provenance.model_version,
    disclosure: dossier.provenance.disclosure,
  };
  dossier.rights.forEach((r, i) => {
    Object.assign(fields, {
      [`right${i}Kind`]: r.kind,
      [`right${i}Holder`]: r.holder,
      [`right${i}Scope`]: r.scope,
      [`right${i}Withdrawal`]: r.withdrawal,
      [`right${i}Evidence`]: r.evidence_id,
      [`right${i}Starts`]: r.starts_at,
      [`right${i}Ends`]: r.ends_at,
    });
  });
  return fields;
}
export default function LifecycleDossier(
  props: LifecycleFormProps & {
    previous: string | null;
    dossier: Dossier | null;
  },
) {
  return (
    <details className="workflow-panel">
      <summary>
        {props.dossier
          ? "Replace authority, rights & provenance"
          : "Record authority, rights & provenance"}
      </summary>
      <p className="help">
        Owner declarations stay within the workspace. Replacement requires fresh
        assessments. Add and inspect supporting originals in Evidence &amp;
        assets first.
      </p>
      <LifecycleForm
        {...props}
        actionKey={`dossier:${props.previous ?? "first"}`}
        initial={initialFields(props.dossier)}
        content={dossierDraft}
        label="Record lifecycle declaration"
        confirmation="I reviewed these authority and rights declarations and their evidence references."
      >
        {(draft) => <DossierFields {...props} draft={draft} />}
      </LifecycleForm>
    </details>
  );
}
function DossierFields(props: LifecycleFormProps & { draft: WriteDraftState }) {
  const { draft } = props,
    count = Number(draft.fields.rightCount || 1);
  return (
    <>
      <OperatorFields {...props} />
      {Array.from({ length: count }, (_, i) => (
        <RightFields key={i} {...props} index={i} />
      ))}
      <div className="record-detail-actions">
        <button
          type="button"
          className="secondary"
          disabled={count >= 8}
          onClick={() => draft.change("rightCount", String(count + 1))}
        >
          Add rights claim
        </button>
        {count > 1 && (
          <button
            type="button"
            className="text-button"
            onClick={() => draft.change("rightCount", String(count - 1))}
          >
            Remove last claim
          </button>
        )}
      </div>
      <ProvenanceFields draft={draft} />
    </>
  );
}
function OperatorFields(
  props: LifecycleFormProps & { draft: WriteDraftState },
) {
  const { draft } = props;
  return (
    <fieldset>
      <legend>Accountable operator</legend>
      <TextFields specs={operatorFields} draft={draft} />
      <label>
        Organization (optional)
        <input
          maxLength={80}
          placeholder="Organization represented"
          value={draft.fields.organization ?? ""}
          onChange={(e) => draft.change("organization", e.target.value)}
        />
      </label>
      <CreditEvidencePicker
        source={props.source}
        versionId={props.version.version_id}
        selected={draft.fields.operatorEvidence || null}
        change={(id) => draft.change("operatorEvidence", id ?? "")}
        label="authority evidence"
      />
    </fieldset>
  );
}
function ProvenanceFields({ draft }: { draft: WriteDraftState }) {
  return (
    <fieldset>
      <legend>Creation provenance · creator declared</legend>
      <label>
        Creation method
        <select
          value={draft.fields.method || "mixed"}
          onChange={(e) => draft.change("method", e.target.value)}
        >
          <option value="mixed">AI and human work</option>
          <option value="generated">Generated</option>
          <option value="human_driven">Human driven</option>
        </select>
      </label>
      <TextFields specs={provenanceFields} draft={draft} />
      <p className="help">
        These entries are declarations. Metadata extraction and external
        provenance verification are not performed here.
      </p>
    </fieldset>
  );
}
function RightFields(
  props: LifecycleFormProps & { draft: WriteDraftState; index: number },
) {
  const { draft, index: i } = props;
  return (
    <fieldset>
      <legend>Rights claim {i + 1}</legend>
      <label>
        Right type
        <select
          value={draft.fields[`right${i}Kind`] || "likeness"}
          onChange={(e) => draft.change(`right${i}Kind`, e.target.value)}
        >
          {rightKinds.map((kind) => (
            <option key={kind} value={kind}>
              {kind.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>
      <TextFields
        specs={[
          spec(`right${i}Holder`, "Rights holder", 80),
          spec(`right${i}Scope`, "Permitted uses and limitations"),
          spec(`right${i}Withdrawal`, "Withdrawal conditions"),
          spec(`right${i}Starts`, "Rights start (include timezone)", 40),
          spec(`right${i}Ends`, "Rights end (include timezone)", 40),
        ]}
        draft={draft}
      />
      <CreditEvidencePicker
        source={props.source}
        versionId={props.version.version_id}
        selected={draft.fields[`right${i}Evidence`] || null}
        change={(id) => draft.change(`right${i}Evidence`, id ?? "")}
        label={`rights evidence ${i + 1}`}
      />
    </fieldset>
  );
}
