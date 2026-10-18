/** Explicit enrollment derives the content hash on the server, never from a typed digest. */
import { apiClient } from "./api-client";
import { hex, object, requireContract, text, uuid } from "./persona-validation";

export type AssetEnrollmentCommand = {
  request_id: string;
  version_id: string;
  evidence_id: string;
  label: string;
  permission_statement: string;
};
export type AssetEnrollmentReceipt = {
  workspace_id: string;
  version_id: string;
  evidence_id: string;
  asset: { id: string; digest: string; label: string };
};
export type AssetRegistry = {
  workspaceId: string;
  enroll(
    command: AssetEnrollmentCommand,
    signal: AbortSignal,
  ): Promise<AssetEnrollmentReceipt>;
};
export function assetRegistry(workspace: string): AssetRegistry {
  const workspaceId = uuid(workspace);
  return {
    workspaceId,
    async enroll(command, signal) {
      const body = {
        request_id: uuid(command.request_id),
        version_id: uuid(command.version_id),
        evidence_id: uuid(command.evidence_id),
        label: text(command.label, 80),
        permission_statement: text(command.permission_statement, 500),
      };
      const row = object(
        await apiClient.post(
          `/api/workspaces/${workspaceId}/personas/assets/enroll`,
          body,
          {
            signal,
            credentials: "same-origin",
            mode: "same-origin",
            cache: "no-store",
            redirect: "error",
            retries: 0,
          },
        ),
        ["workspace_id", "version_id", "evidence_id", "asset"],
      );
      const asset = object(row.asset, ["id", "digest", "label"]);
      requireContract(
        !signal.aborted &&
          uuid(row.workspace_id) === workspaceId &&
          uuid(row.version_id) === body.version_id &&
          uuid(row.evidence_id) === body.evidence_id &&
          text(asset.label, 80) === body.label,
      );
      return {
        workspace_id: workspaceId,
        version_id: body.version_id,
        evidence_id: body.evidence_id,
        asset: {
          id: uuid(asset.id),
          digest: hex(asset.digest, 64),
          label: body.label,
        },
      };
    },
  };
}
