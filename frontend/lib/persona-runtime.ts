/** Same-origin runtime configuration and durable job controls; no automatic provider retry. */
import { apiClient } from "./api-client";
import type { FaceCommand, FaceSubject } from "./persona-faces";
import {
  parseFaceCommand,
  parseJob,
  parseJobUpdate,
  type JobPage,
  type JobReceipt,
  type JobUpdate,
} from "./persona-job-contracts";
import { list, object, requireContract, uuid } from "./persona-validation";

export type RuntimeReadiness = {
  workspace_id: string;
  face_jobs_configured: boolean;
  search_configured: boolean;
  investigation_configured: boolean;
  signing_configured: boolean;
  verification_configured: boolean;
  acceptance: "live_rehearsal_required";
};
export type RuntimeGateway = {
  workspaceId: string;
  readiness: (signal: AbortSignal) => Promise<RuntimeReadiness>;
  enqueue: (command: FaceCommand, signal: AbortSignal) => Promise<JobReceipt>;
  history: (subject: FaceSubject, signal: AbortSignal) => Promise<JobPage>;
  update: (
    command: JobUpdate,
    subject: FaceSubject,
    signal: AbortSignal,
  ) => Promise<JobReceipt>;
};
export function parseReadiness(value: unknown): RuntimeReadiness {
  const r = object(value, [
    "workspace_id",
    "face_jobs_configured",
    "search_configured",
    "investigation_configured",
    "signing_configured",
    "verification_configured",
    "acceptance",
  ]);
  const flags = [
    "face_jobs_configured",
    "search_configured",
    "investigation_configured",
    "signing_configured",
    "verification_configured",
  ];
  requireContract(
    flags.every((key) => typeof r[key] === "boolean") &&
      r.acceptance === "live_rehearsal_required",
  );
  requireContract(!r.investigation_configured || r.search_configured);
  requireContract(!r.signing_configured || r.verification_configured);
  return { ...r, workspace_id: uuid(r.workspace_id) } as RuntimeReadiness;
}
function bind(
  row: FaceSubject & { workspace_id: string },
  subject: FaceSubject,
  workspace: string,
) {
  requireContract(
    row.workspace_id === workspace &&
      row.version_id === subject.version_id &&
      row.portrait_id === subject.portrait_id,
  );
}
function parsePage(
  value: unknown,
  subject: FaceSubject,
  workspace: string,
): JobPage {
  const r = object(value, [
    "workspace_id",
    "version_id",
    "portrait_id",
    "items",
    "overflow",
  ]);
  requireContract(typeof r.overflow === "boolean");
  const result = {
    workspace_id: uuid(r.workspace_id),
    version_id: uuid(r.version_id),
    portrait_id: uuid(r.portrait_id),
    items: list(r.items, parseJob, 20),
    overflow: r.overflow,
  };
  bind(result, subject, workspace);
  const ids = new Set<string>();
  for (const item of result.items) {
    bind(item, subject, workspace);
    requireContract(!ids.has(item.job_id));
    ids.add(item.job_id);
  }
  return result;
}
function privatePost(workspace: string) {
  return async (path: string, body: object, signal: AbortSignal) => {
    requireContract(!signal.aborted);
    const result = await apiClient.post<unknown>(
      `/api/workspaces/${workspace}/personas/${path}`,
      body,
      {
        signal,
        credentials: "same-origin",
        mode: "same-origin",
        cache: "no-store",
        redirect: "error",
        retries: 0,
        timeoutMs: 30000,
      },
    );
    requireContract(!signal.aborted);
    return result;
  };
}
export function runtimeGateway(workspace: string): RuntimeGateway {
  const workspaceId = uuid(workspace),
    post = privatePost(workspaceId);
  return {
    workspaceId,
    async readiness(signal) {
      const result = parseReadiness(
        await post("runtime/readiness", {}, signal),
      );
      requireContract(result.workspace_id === workspaceId);
      return result;
    },
    async enqueue(command, signal) {
      command = parseFaceCommand(command);
      const result = parseJob(await post("jobs/enqueue", command, signal));
      bind(result, command, workspaceId);
      requireContract(
        JSON.stringify(result.command) === JSON.stringify(command),
      );
      return result;
    },
    async history(subject, signal) {
      return parsePage(
        await post("jobs/history", subject, signal),
        subject,
        workspaceId,
      );
    },
    async update(command, subject, signal) {
      command = parseJobUpdate(command);
      const result = parseJob(await post("jobs/update", command, signal));
      bind(result, subject, workspaceId);
      requireContract(
        result.job_id === command.job_id &&
          result.sequence > command.expected_sequence,
      );
      return result;
    },
  };
}
