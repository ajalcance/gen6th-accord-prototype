/** Strict reference-only job receipts; a queue acknowledgement is not a model result. */
import type { FaceCommand, FaceSubject } from "./persona-faces";
import {
  choice,
  integer,
  object,
  requireContract,
  timestamp,
  uuid,
} from "./persona-validation";

export type JobState =
  "queued" | "dispatched" | "running" | "succeeded" | "failed" | "cancelled";
export type JobReceipt = FaceSubject & {
  job_id: string;
  workspace_id: string;
  command: FaceCommand;
  state: JobState;
  sequence: number;
  attempts: number;
  recorded_at: string;
  updated_at: string;
  lease_until: string | null;
  generation_id: string | null;
  recovery_available: boolean;
};
export type JobUpdate = {
  job_id: string;
  request_id: string;
  expected_sequence: number;
  action: "retry" | "cancel";
};
export type JobPage = FaceSubject & {
  workspace_id: string;
  items: JobReceipt[];
  overflow: boolean;
};

export function parseFaceCommand(value: unknown): FaceCommand {
  const r = object(value, [
    "version_id",
    "portrait_id",
    "request_id",
    "generation_id",
    "face_index",
  ]);
  const index = r.face_index === null ? null : integer(r.face_index, 0);
  const generation = r.generation_id === null ? null : uuid(r.generation_id);
  requireContract(
    (index === null) === (generation === null) &&
      (index === null || index <= 9),
  );
  return {
    version_id: uuid(r.version_id),
    portrait_id: uuid(r.portrait_id),
    request_id: uuid(r.request_id),
    generation_id: generation,
    face_index: index,
  };
}
export function parseJobUpdate(value: unknown): JobUpdate {
  const r = object(value, [
    "job_id",
    "request_id",
    "expected_sequence",
    "action",
  ]);
  const sequence = integer(r.expected_sequence, 0);
  requireContract(sequence <= 32);
  return {
    job_id: uuid(r.job_id),
    request_id: uuid(r.request_id),
    expected_sequence: sequence,
    action: choice(r.action, ["retry", "cancel"]),
  };
}
export function parseJob(value: unknown): JobReceipt {
  const r = object(value, [
    "job_id",
    "workspace_id",
    "version_id",
    "portrait_id",
    "command",
    "state",
    "sequence",
    "attempts",
    "recorded_at",
    "updated_at",
    "lease_until",
    "generation_id",
    "recovery_available",
  ]);
  requireContract(typeof r.recovery_available === "boolean");
  const result: JobReceipt = {
    job_id: uuid(r.job_id),
    workspace_id: uuid(r.workspace_id),
    version_id: uuid(r.version_id),
    portrait_id: uuid(r.portrait_id),
    command: parseFaceCommand(r.command),
    state: choice(r.state, [
      "queued",
      "dispatched",
      "running",
      "succeeded",
      "failed",
      "cancelled",
    ]),
    sequence: integer(r.sequence, 0),
    attempts: integer(r.attempts, 0),
    recorded_at: timestamp(r.recorded_at),
    updated_at: timestamp(r.updated_at),
    lease_until: r.lease_until === null ? null : timestamp(r.lease_until),
    generation_id: r.generation_id === null ? null : uuid(r.generation_id),
    recovery_available: r.recovery_available,
  };
  validateJob(result);
  return result;
}
function validateJob(r: JobReceipt) {
  requireContract(
    r.sequence <= 32 &&
      r.attempts <= 3 &&
      r.job_id === r.command.request_id &&
      r.version_id === r.command.version_id &&
      r.portrait_id === r.command.portrait_id &&
      Date.parse(r.updated_at) >= Date.parse(r.recorded_at) &&
      (r.state === "succeeded") === (r.generation_id !== null) &&
      (r.state === "running") === (r.lease_until !== null) &&
      (!r.recovery_available ||
        (r.attempts < 3 &&
          r.sequence < 29 &&
          !["succeeded", "cancelled"].includes(r.state))),
  );
  if (r.lease_until)
    requireContract(Date.parse(r.lease_until) > Date.parse(r.updated_at));
}
