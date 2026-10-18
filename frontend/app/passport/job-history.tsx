import type { FaceSubject } from "../../lib/persona-faces";
import type { JobPage, JobReceipt } from "../../lib/persona-job-contracts";
import type { JobProps } from "./durable-face-jobs";
import { useJobMutation } from "./job-state";
import { JobActions, JobFeedback } from "./job-controls";

type Props = JobProps & {
  subject: FaceSubject;
  page: JobPage;
  refresh: () => void;
};
export default function JobHistory(props: Props) {
  return (
    <section aria-label="Saved processing jobs">
      <h4>Recent processing jobs</h4>
      {!props.page.items.length && (
        <p>No saved jobs for this exact reference.</p>
      )}
      {props.page.overflow && <p>Showing the 20 most recent jobs.</p>}
      {props.page.items.map((job) => (
        <JobRow key={job.job_id} {...props} job={job} />
      ))}
    </section>
  );
}
function JobRow(props: Props & { job: JobReceipt }) {
  const { job, source, subject } = props;
  const mutation = useJobMutation(
    source.runtime!,
    `${source.workspaceId}:${source.sessionKey}:job-update:${job.job_id}`,
    subject,
    props.denied,
    true,
  );
  const pending =
    mutation.state.phase === "pending" ||
    mutation.state.phase === "succeeded" ||
    mutation.requiresResolution;
  function change(action: "retry" | "cancel") {
    void mutation.submit({
      job_id: job.job_id,
      request_id: crypto.randomUUID(),
      expected_sequence: job.sequence,
      action,
    });
  }
  return (
    <article className="governance-record">
      <h5>
        {job.command.generation_id ? "Face representations" : "Face detection"}{" "}
        · {job.state}
      </h5>
      <p>
        Attempts {job.attempts} of 3 · updated {job.updated_at}
      </p>
      <small>Job {job.job_id}</small>
      <JobActions
        job={job}
        pending={pending}
        change={change}
        reload={props.reloadResult}
      />
      <JobFeedback
        mutation={mutation}
        refresh={props.refresh}
        label="Reload job status"
      />
    </article>
  );
}
