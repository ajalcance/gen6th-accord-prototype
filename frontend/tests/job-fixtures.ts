import type { FaceCommand } from "../lib/persona-faces";
import type { JobReceipt } from "../lib/persona-job-contracts";
import type { RuntimeReadiness } from "../lib/persona-runtime";
import { capture } from "./capture-fixtures";
import { version } from "./prepared-write-fixtures";

export const subject = {
  version_id: version.version_id,
  portrait_id: capture.portrait_id,
};
export const command: FaceCommand = {
  ...subject,
  request_id: "00000000-0000-4000-8000-000000000099",
  generation_id: null,
  face_index: null,
};
export function job(intent = command): JobReceipt {
  return {
    ...subject,
    job_id: intent.request_id,
    workspace_id: version.workspace_id,
    command: intent,
    state: "queued",
    sequence: 0,
    attempts: 0,
    recorded_at: version.recorded_at,
    updated_at: version.recorded_at,
    lease_until: null,
    generation_id: null,
    recovery_available: false,
  };
}
export const ready: RuntimeReadiness = {
  workspace_id: version.workspace_id,
  face_jobs_configured: true,
  search_configured: false,
  investigation_configured: false,
  signing_configured: false,
  verification_configured: false,
  acceptance: "live_rehearsal_required",
};
export const page = {
  ...subject,
  workspace_id: version.workspace_id,
  items: [],
  overflow: false,
};
