import type { FaceResult } from "../../lib/persona-faces";
import type { JobReceipt } from "../../lib/persona-job-contracts";
import type { useJobMutation } from "./job-state";
import { WriteFeedback } from "./prepared-write-common";

export function JobConsent({
  checked,
  disabled,
  change,
}: {
  checked: boolean;
  disabled: boolean;
  change: (value: boolean) => void;
}) {
  return (
    <label>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => change(event.target.checked)}
      />
      Use this approved reference with configured Google processing. Up to three
      worker attempts may incur repeated cost after a failure.
    </label>
  );
}
export function JobFeedback({
  mutation,
  refresh,
  label,
}: {
  mutation: ReturnType<typeof useJobMutation>;
  refresh: () => void;
  label: string;
}) {
  return (
    <>
      <WriteFeedback
        state={mutation.state}
        retry={() => void mutation.retry()}
        cancel={mutation.cancel}
        mayRetry={mutation.mayRetry}
      />
      {(mutation.state.phase === "succeeded" ||
        mutation.state.phase === "conflict") && (
        <button
          onClick={() => {
            mutation.prepare();
            refresh();
          }}
        >
          {label}
        </button>
      )}
    </>
  );
}
export function JobFaceChoice({
  result,
  selected,
  change,
}: {
  result: FaceResult;
  selected: number | null;
  change: (value: number | null) => void;
}) {
  return (
    <label>
      Performer face
      <select
        value={selected ?? ""}
        onChange={(event) =>
          change(event.target.value === "" ? null : Number(event.target.value))
        }
      >
        <option value="">Choose a detected face</option>
        {result.faces.map((face) => (
          <option key={face.index} value={face.index}>
            Face {face.index + 1}
          </option>
        ))}
      </select>
    </label>
  );
}
export function JobActions({
  job,
  pending,
  change,
  reload,
}: {
  job: JobReceipt;
  pending: boolean;
  change: (action: "retry" | "cancel") => void;
  reload: () => void;
}) {
  return (
    <>
      {job.state === "succeeded" && (
        <button className="secondary" onClick={reload}>
          Reload completed face result
        </button>
      )}
      {job.recovery_available && (
        <button disabled={pending} onClick={() => change("retry")}>
          Recover stalled or failed job
        </button>
      )}
      {!["succeeded", "cancelled"].includes(job.state) && (
        <button
          className="secondary"
          disabled={pending}
          onClick={() => change("cancel")}
        >
          Cancel future job processing
        </button>
      )}
    </>
  );
}
