import { useState } from "react";
import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";
import { campaignBlocks } from "./console-fixtures";
import { SecurityReadiness } from "../../app/passport/console-footer";

const QUESTIONS = [
  {
    id: "control",
    title: "What does the unrelated control show?",
    answer:
      "The circle and triangle are an original geometric fixture, unrelated to the portrait study. This is a declared control, not a computed similarity verdict. A real benchmark must measure whether such controls are incorrectly retrieved.",
    source: "Reference catalogue · geometric-control-01",
  },
  {
    id: "evidence",
    title: "What is missing before review?",
    answer:
      "The illustration and creator contribution are supplied fixtures. No generation log or reference permission is supplied. Keep those gaps visible; the scenario cannot establish authorship or legal ownership.",
    source: "System Capture record · evidence-gap-01",
  },
  {
    id: "candidate",
    title: "Why was this candidate surfaced?",
    answer:
      "The fixture reference is a palette derivative of the same original drawing. Shared composition is intentional scenario data. No embedding search or model inference ran, and this is not a copying probability.",
    source: "Reference catalogue · palette-study-02",
  },
  {
    id: "scope",
    title: "Why is this campaign blocked?",
    answer:
      "Acceptance and permission to use are different. Check the exact reviewed version, current owner offer, named recipient decision and campaign window. A historical acceptance cannot bypass a changed review or revoked offer.",
    source: "Campaign permission · current fixture state",
  },
  {
    id: "change",
    title: "Draft a change request",
    answer:
      "Please provide the missing generation record or explicitly state that none exists. Identify any reference assets and their permissions, then submit a new exact version for independent review.",
    source: "Evidence gap · proposed reviewer note",
  },
];

export function AssistantContent(props: StudioState) {
  const orderedQuestions = [...QUESTIONS].sort(
    (a, b) =>
      Number(
        b.id ===
          (props.step === 3
            ? "scope"
            : props.step === 1
              ? "evidence"
              : "candidate"),
      ) -
      Number(
        a.id ===
          (props.step === 3
            ? "scope"
            : props.step === 1
              ? "evidence"
              : "candidate"),
      ),
  );
  const question =
    QUESTIONS.find((item) => item.id === props.assistantQuestion) ??
    QUESTIONS[0];
  return (
    <div className="drawer-body">
      <p className="callout">
        <Icon name="spark" />
        Fixture assistant · scripted, source-linked responses. No model is
        connected.
      </p>
      <div className="question-list">
        {orderedQuestions.map((item) => (
          <button
            key={item.id}
            className={item.id === question.id ? "selected" : ""}
            onClick={() => props.ask(item.id)}
          >
            {item.title}
            <Icon name="arrow" />
          </button>
        ))}
      </div>
      <AssistantAnswer {...props} question={question} />
      <AssistantAction {...props} />
    </div>
  );
}

function AssistantAction(props: StudioState) {
  const change = QUESTIONS.find((item) => item.id === "change");
  return (
    <div className="drawer-body drawer-footer">
      {props.assistantQuestion === "change" ? (
        <button
          className="primary"
          onClick={() => {
            props.setComment(change?.answer ?? "");
            props.setStep(2);
            props.setDrawer(null);
          }}
        >
          Use as editable demo note
          <Icon name="arrow" />
        </button>
      ) : (
        <button
          className="secondary"
          onClick={() => {
            props.setStep(props.assistantQuestion === "scope" ? 3 : 2);
            props.setDrawer(null);
          }}
        >
          Open the source workspace
          <Icon name="arrow" />
        </button>
      )}
      <p className="help">
        Human review remains required. Applying a note clears an earlier demo
        decision.
      </p>
    </div>
  );
}

export function RecordContent(props: StudioState) {
  const [kind, setKind] = useState("all");
  const entries = props.history.filter(
    (entry) => kind === "all" || entry.title.toLowerCase().includes(kind),
  );
  return (
    <div className="drawer-body">
      <div className="record-summary">
        <Icon name="passport" size={30} />
        <div>
          <h3>{props.record.committed.name}</h3>
          <p>
            fixture-v{props.revision} · {props.history.length} local entries
          </p>
        </div>
        <span className="status">Unsigned</span>
      </div>
      <p className="help">
        Tab-local scenario history. These are not PostgreSQL receipts or
        verified audit entries.
      </p>
      <label>
        Filter activity
        <select value={kind} onChange={(event) => setKind(event.target.value)}>
          <option value="all">All activity</option>
          <option value="version">Versions</option>
          <option value="review">Reviews</option>
          <option value="campaign">Campaigns</option>
          <option value="analysis">Analysis</option>
        </select>
      </label>
      {!entries.length && (
        <p role="status">No matching activity in this tab.</p>
      )}
      <ActivityTimeline entries={entries} />
      <div className="capability-note">
        <h3>What a server receipt will add</h3>
        <p>
          Immutable version ID, request ID, attributed decision and matching
          event/audit references. Backend evidence presence is distinct from
          chain verification or signing.
        </p>
      </div>
    </div>
  );
}

const CAPABILITIES = [
  [
    "Saved record reads",
    "Current versions, bounded record search and private evidence status",
  ],
  [
    "Private evidence quarantine",
    "Encrypted temporary storage; real key, scanner and retention providers required",
  ],
  [
    "Version storage",
    "Immutable versions, revision conflicts and exact retry receipts",
  ],
  [
    "Review governance",
    "Independent reviewer, self-review denial and bounded decision history",
  ],
  [
    "Campaign permissions",
    "Exact asset/version bindings, named parties and current eligibility",
  ],
  [
    "Audit & detection",
    "Durable processing, retained evidence references and scoped backlog reads",
  ],
];

export function OperationsContent(props: StudioState) {
  return (
    <div className="drawer-body">
      <div className="connection-card">
        <span className="status warning">Persona API not connected</span>
        <h3>Connection status</h3>
        <p>
          This console shows local fixture activity. Internal backend services
          are tested, but their persona routes and trusted sessions are not
          activated.
        </p>
      </div>
      <OperationMetrics {...props} />
      <SecurityReadiness />
      <h3>Internal backend capabilities</h3>
      <div className="capability-list">
        {CAPABILITIES.map(([name, description]) => (
          <div key={name}>
            <Icon name="file" />
            <div>
              <strong>{name}</strong>
              <p>{description}</p>
            </div>
            <span className="status">Internal implementation</span>
          </div>
        ))}
      </div>
      <p className="help">
        No live backend backlog, findings, signatures or server receipts are
        claimed. Identity, API adapters, secure uploads, real AI and public
        signing remain required for commercial delivery.
      </p>
    </div>
  );
}

function OperationMetrics(props: StudioState) {
  return (
    <div className="operation-metrics">
      <div>
        <strong>
          {
            props.records.filter((record) => record.analysis === "running")
              .length
          }
        </strong>
        <span>Local scan simulations</span>
      </div>
      <div>
        <strong>
          {props.records.reduce(
            (sum, record) => sum + record.history.length,
            0,
          )}
        </strong>
        <span>Tab-local history entries</span>
      </div>
    </div>
  );
}

function AssistantAnswer(
  props: StudioState & { question: (typeof QUESTIONS)[number] },
) {
  const { question } = props;
  return (
    <section className="assistant-answer" aria-live="polite">
      <p className="eyebrow">PROPOSED CONTEXT / NOT A DECISION</p>
      <h3>{question.title}</h3>
      <p>{question.answer}</p>
      {question.id === "scope" && (
        <ul className="block-list">
          {campaignBlocks(props.record).map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
      <button
        className="source-chip"
        onClick={() => {
          props.setStep(
            question.id === "scope" ? 3 : question.id === "evidence" ? 1 : 2,
          );
          props.setDrawer(null);
        }}
      >
        <Icon name="file" />
        {question.source} <Icon name="arrow" />
      </button>
    </section>
  );
}

function ActivityTimeline({ entries }: { entries: StudioState["history"] }) {
  return (
    <ol className="activity-timeline">
      {[...entries].reverse().map((entry) => (
        <li key={entry.id}>
          <span className="timeline-marker" />
          <div>
            <small>
              fixture-v{entry.revision} · entry{" "}
              {String(entry.id).padStart(2, "0")}
            </small>
            <details>
              <summary>{entry.title}</summary>
              <p>{entry.detail}</p>
            </details>
          </div>
        </li>
      ))}
    </ol>
  );
}
