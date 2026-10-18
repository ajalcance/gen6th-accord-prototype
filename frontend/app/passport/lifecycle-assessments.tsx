import type {
  LifecycleProfile,
  RequirementStatus,
  Assessment,
} from "../../lib/persona-lifecycle-contracts";
import LifecycleForm, { type LifecycleFormProps } from "./lifecycle-form";
import LifecycleFields from "./lifecycle-fields";
import type { TextFieldSpec } from "./prepared-write-common";
import { RecordedTime } from "./governance-common";

const assessmentSpecs: TextFieldSpec[] = [
  {
    field: "statement",
    label: "Assessment basis",
    placeholder: "Identify what you examined and any limitations.",
  },
  {
    field: "expires",
    label: "Assessment expiry (include timezone)",
    max: 40,
    multiline: false,
    placeholder: "YYYY-MM-DDTHH:mm:ssZ",
  },
];

export default function LifecycleAssessments(
  props: LifecycleFormProps & { profile: LifecycleProfile },
) {
  return (
    <section className="workflow-stack" aria-label="Lifecycle requirements">
      <h3>Separate review requirements</h3>
      <p className="help">
        Independent reviewers assess this exact declaration. Record the evidence
        actually examined and the assessment basis; private attachments are not
        automatically shared.
      </p>
      <div className="governance-columns">
        {props.profile.requirements.map((item) => (
          <RequirementCard
            key={`${props.profile.dossier?.id}:${item.requirement}`}
            {...props}
            item={item}
          />
        ))}
      </div>
    </section>
  );
}
function RequirementCard(
  props: LifecycleFormProps & {
    profile: LifecycleProfile;
    item: RequirementStatus;
  },
) {
  const { item, profile } = props,
    assessment = item.assessment;
  return (
    <article className="governance-card">
      <div className="governance-heading">
        <h4>
          {item.requirement === "operator"
            ? "Operator authority"
            : item.requirement === "rights"
              ? "Rights evidence"
              : "Content & disclosure"}
        </h4>
        <span
          className={`status ${item.status === "approved" ? "neutral" : "warning"}`}
        >
          {item.status.replaceAll("_", " ")}
        </span>
      </div>
      {assessment?.content.kind === "assessment" && (
        <>
          <p>{assessment.content.statement}</p>
          <p className="help">
            Reviewed by {assessment.actor_ref} ·{" "}
            <RecordedTime value={assessment.recorded_at} />
          </p>
          <p className="help">
            Assessment expires{" "}
            <RecordedTime value={assessment.content.valid_until} />
          </p>
        </>
      )}
      {profile.dossier && props.source.writeGateway && (
        <AssessmentEditor {...props} />
      )}
    </article>
  );
}
function AssessmentEditor(
  props: LifecycleFormProps & {
    profile: LifecycleProfile;
    item: RequirementStatus;
  },
) {
  const { item, profile } = props,
    assessment = item.assessment;
  const dossier = profile.dossier;
  if (!dossier) return null;
  return (
    <details>
      <summary>Record independent {item.requirement} assessment</summary>
      <LifecycleForm
        {...props}
        actionKey={`assessment:${dossier.id}:${item.requirement}:${assessment?.id ?? "first"}`}
        previous={assessment?.id ?? null}
        initial={{ decision: "changes_requested" }}
        content={(fields): Assessment => ({
          kind: "assessment",
          profile_id: dossier.id,
          requirement: item.requirement,
          decision: fields.decision as Assessment["decision"],
          statement: fields.statement,
          valid_until: fields.expires,
        })}
        label="Record assessment"
        confirmation="I independently assessed this exact declaration and stated my basis and limitations."
      >
        {(draft) => (
          <LifecycleFields
            draft={draft}
            field="decision"
            label="Assessment decision"
            options={[
              { value: "changes_requested", label: "Request changes" },
              { value: "approved", label: "Approve this requirement" },
              { value: "withdrawn", label: "Withdraw approval" },
            ]}
            specs={assessmentSpecs}
          />
        )}
      </LifecycleForm>
    </details>
  );
}
