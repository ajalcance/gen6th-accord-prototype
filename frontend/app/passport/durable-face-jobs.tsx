import { useCallback, useMemo } from "react";
import type { FaceResult, FaceSubject } from "../../lib/persona-faces";
import type { JobPage } from "../../lib/persona-job-contracts";
import type { FaceInspectionProps } from "./face-inspection";
import { GovernanceRead } from "./governance-common";
import { useGovernanceRead } from "./saved-governance-read";
import { useRuntimeReadiness } from "./runtime-readiness";
import JobCreate from "./job-create";
import JobHistory from "./job-history";

export type JobProps = FaceInspectionProps & {
  result: FaceResult | null;
  reloadResult: () => void;
};
export default function DurableFaceJobs(props: JobProps) {
  const gateway = props.source.runtime!;
  const { state, query } = useRuntimeReadiness(gateway);
  return (
    <section aria-label="Durable face processing">
      <h4>Recoverable face processing</h4>
      <GovernanceRead state={state} query={query}>
        {(ready) =>
          ready.face_jobs_configured ? (
            <JobWorkspace {...props} />
          ) : (
            <p>Durable processing is not configured on this connection.</p>
          )
        }
      </GovernanceRead>
    </section>
  );
}
function JobWorkspace(props: JobProps) {
  const subject = useMemo<FaceSubject>(
    () => ({
      version_id: props.version.version_id,
      portrait_id: props.capture.portrait_id,
    }),
    [props.version.version_id, props.capture.portrait_id],
  );
  const gateway = props.source.runtime!;
  const load = useCallback(
    (signal: AbortSignal) => gateway.history(subject, signal),
    [gateway, subject],
  );
  const { state, query } = useGovernanceRead<JobPage>(load);
  return (
    <>
      <button
        className="secondary"
        disabled={state.phase === "loading"}
        onClick={() => void query.run(load)}
      >
        Refresh processing jobs
      </button>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <>
            <JobCreate
              {...props}
              subject={subject}
              page={page}
              refresh={() => void query.run(load)}
            />
            <JobHistory
              {...props}
              subject={subject}
              page={page}
              refresh={() => void query.run(load)}
            />
          </>
        )}
      </GovernanceRead>
      <p className="help">
        Stopping this view does not cancel committed work. Cancellation cannot
        interrupt a provider call already in progress.
      </p>
    </>
  );
}
