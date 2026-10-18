import { useState } from "react";
import type { FaceSubject } from "../../lib/persona-faces";
import type { JobPage } from "../../lib/persona-job-contracts";
import type { JobProps } from "./durable-face-jobs";
import { useJobMutation } from "./job-state";
import { JobConsent, JobFeedback, JobFaceChoice } from "./job-controls";
import ReferencePhoto from "./reference-photo";

type Props = JobProps & {
  subject: FaceSubject;
  page: JobPage;
  refresh: () => void;
};
function useCreation(props: Props) {
  const { source, subject, page } = props;
  const mutation = useJobMutation(
    source.runtime!,
    `${source.workspaceId}:${source.sessionKey}:face-job:${subject.version_id}:${subject.portrait_id}`,
    subject,
    props.denied,
  );
  const [confirmed, confirm] = useState(false);
  const busy = page.items.some(
    (item) =>
      !["succeeded", "cancelled"].includes(item.state) && item.attempts < 3,
  );
  const blocked =
    busy ||
    !confirmed ||
    mutation.requiresResolution ||
    mutation.state.phase === "succeeded" ||
    mutation.state.phase === "pending" ||
    !source.writeGateway;
  function send(index: number | null) {
    void mutation.submit({
      ...subject,
      request_id: crypto.randomUUID(),
      generation_id: index === null ? null : props.result!.generation_id,
      face_index: index,
    });
    confirm(false);
  }
  return { mutation, confirmed, confirm, busy, blocked, send };
}
export default function JobCreate(props: Props) {
  const { mutation, confirmed, confirm, busy, blocked, send } =
    useCreation(props);
  return (
    <section aria-label="Queue approved reference processing">
      <JobConsent
        checked={confirmed}
        change={confirm}
        disabled={busy || mutation.state.phase === "pending"}
      />
      <button disabled={blocked} onClick={() => send(null)}>
        Queue face detection
      </button>
      {busy && (
        <p>
          A job for this reference is pending. Refresh its status before
          preparing another.
        </p>
      )}
      {props.result?.state === "selection_required" && (
        <JobSelection
          key={props.result.generation_id}
          {...props}
          disabled={blocked}
          submit={send}
        />
      )}
      <JobFeedback
        mutation={mutation}
        refresh={props.refresh}
        label="Reload saved jobs"
      />
    </section>
  );
}
function JobSelection({
  result,
  source,
  subject,
  denied,
  disabled,
  submit,
}: Props & { disabled: boolean; submit: (index: number) => void }) {
  const [selected, choose] = useState<number | null>(null),
    [confirmed, confirm] = useState(false);
  if (!result) return null;
  return (
    <fieldset disabled={disabled}>
      <legend>Select the performer for queued representations</legend>
      <ReferencePhoto
        gateway={source.captures!}
        version={subject.version_id}
        portrait={subject.portrait_id}
        denied={denied}
        faces={result}
      />
      <JobFaceChoice
        result={result}
        selected={selected}
        change={(value) => {
          choose(value);
          confirm(false);
        }}
      />
      <label>
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(event) => confirm(event.target.checked)}
          disabled={selected === null}
        />
        I confirm this is the performer face for this approved reference.
      </label>
      <button
        disabled={selected === null || !confirmed}
        onClick={() => {
          if (selected !== null) submit(selected);
        }}
      >
        Queue face and image representations
      </button>
    </fieldset>
  );
}
