/** Exact-file search binds server results to the supplied bytes and current workspace. */
import { apiClient } from "./api-client";
import type { PersonaVersion } from "./persona-contracts";
import type { PhotoUploadCommand } from "./persona-photos";
import { parseVersion } from "./persona-receipts";
import { hex, list, object, requireContract, uuid } from "./persona-validation";

export type PortraitSearchPage = {
  workspace_id: string;
  request_id: string;
  sha256: string;
  method: "exact_file_sha256";
  items: PersonaVersion[];
  has_more: boolean;
};
export type PortraitSearchGateway = {
  workspaceId: string;
  search: (
    command: PhotoUploadCommand,
    signal: AbortSignal,
  ) => Promise<PortraitSearchPage>;
};

export function parsePortraitSearch(value: unknown): PortraitSearchPage {
  const row = object(value, [
    "workspace_id",
    "request_id",
    "sha256",
    "method",
    "items",
    "has_more",
  ]);
  const workspace = uuid(row.workspace_id),
    items = list(row.items, parseVersion, 20);
  requireContract(
    row.method === "exact_file_sha256" && typeof row.has_more === "boolean",
  );
  const ids = items.map((item) => item.persona_id);
  requireContract(
    items.every((item) => item.workspace_id === workspace) &&
      new Set(ids).size === ids.length &&
      ids.join() === [...ids].sort().join() &&
      (!row.has_more || items.length === 20),
  );
  return {
    workspace_id: workspace,
    request_id: uuid(row.request_id),
    sha256: hex(row.sha256, 64),
    method: row.method,
    items,
    has_more: row.has_more,
  };
}

export function portraitSearchGateway(
  workspace: string,
): PortraitSearchGateway {
  const workspaceId = uuid(workspace);
  return {
    workspaceId,
    async search(command, signal) {
      const page = parsePortraitSearch(
        await apiClient.post<unknown>(
          `/api/workspaces/${workspaceId}/personas/photos/search`,
          command,
          {
            signal,
            credentials: "same-origin",
            mode: "same-origin",
            cache: "no-store",
            redirect: "error",
            retries: 0,
            timeoutMs: 45000,
          },
        ),
      );
      requireContract(
        !signal.aborted &&
          page.workspace_id === workspaceId &&
          page.request_id === command.request_id &&
          page.sha256 === command.sha256,
      );
      return page;
    },
  };
}
