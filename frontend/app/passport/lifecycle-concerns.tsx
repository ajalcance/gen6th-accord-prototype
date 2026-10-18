import type {
  Concern,
  ConcernStatus,
  LifecycleProfile,
  Response,
} from "../../lib/persona-lifecycle-contracts";
import LifecycleForm, { type LifecycleFormProps } from "./lifecycle-form";
import LifecycleFields from "./lifecycle-fields";
import { RecordedTime } from "./governance-common";

export default function LifecycleConcerns(
  props: LifecycleFormProps & { profile: LifecycleProfile },
) {
  return (
    <section className="workflow-stack" aria-label="Performer concerns">
      <h3>Concerns &amp; operating status</h3>
      <p role="status">
        {props.profile.suspended
          ? "Performer suspended: new clearance and passport issuance are blocked across versions."
          : "No active performer suspension recorded."}
      </p>
      <p className="help">
        Reports are allegations for review. Only independent workspace reviewers
        can decide a case. Up to 20 recent concerns appear here; the history
        includes older cases.
      </p>
      <ReportConcern {...props} />
      {props.profile.concerns.map((entry) => (
        <ConcernCard
          key={`${entry.report.id}:${entry.response?.id}`}
          {...props}
          entry={entry}
        />
      ))}
    </section>
  );
}
function ReportConcern(props: LifecycleFormProps) {
  return (
    <details>
      <summary>Report a concern</summary>
      <LifecycleForm
        {...props}
        actionKey="concern"
        previous={null}
        initial={{ category: "rights" }}
        content={(f): Concern => ({
          kind: "concern",
          category: f.category as Concern["category"],
          statement: f.statement,
        })}
        label="Record concern"
        confirmation="I reviewed this concern and understand it will be visible to authorised workspace members."
      >
        {(draft) => (
          <LifecycleFields
            draft={draft}
            field="category"
            label="Concern category"
            options={["rights", "identity", "content", "safety", "other"].map(
              (value) => ({ value, label: value }),
            )}
            specs={[
              {
                field: "statement",
                label: "Concern details",
                placeholder:
                  "Describe the concern and the relevant evidence without private personal details.",
              },
            ]}
          />
        )}
      </LifecycleForm>
    </details>
  );
}
export function ConcernCard(
  props: LifecycleFormProps & { entry: ConcernStatus },
) {
  const { report, response } = props.entry;
  const state =
    response?.content.kind === "response" ? response.content.decision : "open";
  return (
    <article className="governance-card">
      <div className="governance-heading">
        <h4>
          {report.content.kind === "concern"
            ? report.content.category
            : "Concern"}
        </h4>
        <span className="status neutral">{state}</span>
      </div>
      {report.content.kind === "concern" && <p>{report.content.statement}</p>}
      <p className="help">
        Reported by {report.actor_ref} ·{" "}
        <RecordedTime value={report.recorded_at} />
      </p>
      {response?.content.kind === "response" && (
        <p>
          Response by {response.actor_ref}: {response.content.statement}
        </p>
      )}
      {state !== "resolved" && <ConcernResponse {...props} state={state} />}
    </article>
  );
}
function ConcernResponse(
  props: LifecycleFormProps & { entry: ConcernStatus; state: string },
) {
  const { report, response } = props.entry;
  return (
    <details>
      <summary>Independent reviewer response</summary>
      <LifecycleForm
        {...props}
        actionKey={`response:${report.id}:${response?.id ?? "first"}`}
        previous={response?.id ?? null}
        initial={{
          decision: props.state === "suspended" ? "suspended" : "open",
        }}
        content={(f): Response => ({
          kind: "response",
          concern_id: report.id,
          decision: f.decision as Response["decision"],
          statement: f.statement,
        })}
        label="Record concern response"
        confirmation="I independently reviewed this case and authorise the stated operating status."
      >
        {(draft) => (
          <LifecycleFields
            draft={draft}
            field="decision"
            label="Operating decision"
            options={[
              {
                value: "open",
                label: "Keep case open",
                disabled: props.state === "suspended",
              },
              { value: "suspended", label: "Suspend performer use" },
              { value: "resolved", label: "Resolve this case" },
            ]}
            specs={[
              {
                field: "statement",
                label: "Response basis",
                placeholder: "Explain the evidence and your decision.",
              },
            ]}
          />
        )}
      </LifecycleForm>
    </details>
  );
}
