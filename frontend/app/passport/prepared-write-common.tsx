import type { ReactNode } from "react";
import type { MutationState } from "../../lib/persona-mutation";
import type { SavedPersonaSource } from "./saved-source";
import type { WriteKind } from "./prepared-write-state";
import type { useWriteDraft, usePreparedWrite } from "./prepared-write-state";

export type TextFieldSpec = {
  field: string;
  label: string;
  max?: number;
  multiline?: boolean;
  placeholder?: string;
};
export type WriteDraftState = ReturnType<typeof useWriteDraft>;
export type PreparedMutationState = ReturnType<typeof usePreparedWrite>;
export const uncertain = (state: MutationState<unknown>) =>
  ["pending", "retryable", "cancelled"].includes(state.phase);

export function writeKey(
  source: SavedPersonaSource,
  kind: WriteKind,
  resource: string,
) {
  return `${source.workspaceId}:${source.sessionKey}:${kind}:${resource}`;
}
export function WriteField({
  label,
  value,
  change,
  max = 500,
  multiline = true,
  placeholder,
}: {
  label: string;
  value: string;
  change: (value: string) => void;
  max?: number;
  multiline?: boolean;
  placeholder?: string;
}) {
  return (
    <label>
      {label}
      {multiline ? (
        <textarea
          placeholder={placeholder}
          required
          maxLength={max}
          value={value}
          onChange={(event) => change(event.target.value)}
        />
      ) : (
        <input
          placeholder={placeholder}
          required
          maxLength={max}
          value={value}
          onChange={(event) => change(event.target.value)}
        />
      )}
    </label>
  );
}
export function WriteConfirmation({
  value,
  change,
  children,
}: {
  value: string;
  change: (value: string) => void;
  children: ReactNode;
}) {
  return (
    <label className="prepared-confirm">
      <input
        type="checkbox"
        checked={value === "yes"}
        onChange={(event) => change(event.target.checked ? "yes" : "")}
      />
      {children}
    </label>
  );
}
export function WriteFeedback({
  state,
  retry,
  cancel,
  mayRetry,
}: {
  state: MutationState<unknown>;
  retry: () => void;
  cancel: () => void;
  mayRetry?: boolean;
}) {
  if (state.phase === "idle") return null;
  return (
    <div
      className="saved-feedback"
      role={
        state.phase === "pending" || state.phase === "succeeded"
          ? "status"
          : "alert"
      }
    >
      {state.phase === "pending" ? (
        <>
          <p>Waiting for the server receipt…</p>
          <button type="button" className="secondary" onClick={cancel}>
            Stop waiting
          </button>
        </>
      ) : state.phase === "succeeded" ? (
        <p>
          Storage receipt validated. Reload records to inspect the result; no
          rights or signing established.
        </p>
      ) : (
        <p>{"message" in state ? state.message : ""}</p>
      )}
      {(mayRetry ??
        (state.phase === "retryable" || state.phase === "cancelled")) && (
        <button type="button" className="secondary" onClick={retry}>
          Retry same intent
        </button>
      )}
    </div>
  );
}
export function unresolved(state: MutationState<unknown>) {
  return ["pending", "retryable", "cancelled", "succeeded"].includes(
    state.phase,
  );
}
export function TextFields({
  specs,
  draft,
}: {
  specs: TextFieldSpec[];
  draft: WriteDraftState;
}) {
  return (
    <>
      {specs.map(({ field, ...spec }) => (
        <WriteField
          key={field}
          {...spec}
          value={draft.fields[field] ?? ""}
          change={(value) => draft.change(field, value)}
        />
      ))}
    </>
  );
}
export function SubmitWriteForm({
  draft,
  mutation,
  ready,
  label,
  confirmation,
  submit,
  children,
}: {
  draft: WriteDraftState;
  mutation: PreparedMutationState;
  ready: boolean;
  label: string;
  confirmation: string;
  submit: () => void;
  children: ReactNode;
}) {
  const allowed = writeAllowed(draft, mutation, ready);
  return (
    <form
      className="prepared-write-form"
      onSubmit={(event) => {
        event.preventDefault();
        if (allowed) submit();
      }}
    >
      <fieldset disabled={mutation.state.phase === "pending"}>
        {children}
        <WriteConfirmation
          value={draft.fields.confirm ?? ""}
          change={(value) => draft.change("confirm", value)}
        >
          {confirmation}
        </WriteConfirmation>
      </fieldset>
      <button className="primary" disabled={!allowed}>
        {label}
      </button>
    </form>
  );
}
function writeAllowed(
  draft: WriteDraftState,
  mutation: PreparedMutationState,
  ready: boolean,
) {
  return (
    !unresolved(mutation.state) &&
    !mutation.requiresResolution &&
    ready &&
    draft.fields.confirm === "yes"
  );
}
export function ReloadWrite({
  draft,
  mutation,
  loading,
  reload,
  label,
}: {
  draft: WriteDraftState;
  mutation: PreparedMutationState;
  loading: boolean;
  reload: () => void;
  label: string;
}) {
  return (
    <button
      className="secondary"
      disabled={
        uncertain(mutation.state) || mutation.requiresResolution || loading
      }
      onClick={() => {
        draft.change("confirm", "");
        mutation.prepare();
        reload();
      }}
    >
      {label}
    </button>
  );
}
export function DecisionFields({
  draft,
  campaign = false,
}: {
  draft: WriteDraftState;
  campaign?: boolean;
}) {
  return (
    <>
      <label>
        {campaign ? "Campaign decision" : "Review decision"}
        <select
          value={draft.fields.decision ?? "changes_requested"}
          onChange={(event) => draft.change("decision", event.target.value)}
        >
          <option value="changes_requested">
            {campaign ? "Recipient requests changes" : "Request changes"}
          </option>
          <option value={campaign ? "accepted" : "approved"}>
            {campaign ? "Recipient accepts scope" : "Approve this version"}
          </option>
          {campaign && (
            <option value="revoked">Owner revokes permission</option>
          )}
        </select>
      </label>
      <WriteField
        placeholder={
          campaign
            ? "Explain your decision about this scope."
            : "Summarize the evidence and reasons for this decision."
        }
        label={
          campaign
            ? "Campaign decision statement"
            : "Independent review statement"
        }
        value={draft.fields.statement ?? ""}
        change={(value) => draft.change("statement", value)}
      />
    </>
  );
}
