/** Explicit private query preparation, selection, comparison and clearing. */
import { apiClient } from "./api-client";
import { fetchPrivatePng, type PhotoUploadCommand } from "./persona-photos";
import {
  parseQueryReceipt,
  parseSimilarityPage,
  type QueryReceipt,
  type SearchCommand,
  type SimilarityPage,
  type SimilarityReadiness,
} from "./persona-similarity-contracts";
import {
  choice,
  object,
  requireContract,
  text,
  uuid,
} from "./persona-validation";

export type SimilarityGateway = {
  workspaceId: string;
  readiness(signal: AbortSignal): Promise<SimilarityReadiness>;
  prepare(
    command: PhotoUploadCommand,
    signal: AbortSignal,
  ): Promise<QueryReceipt>;
  search(command: SearchCommand, signal: AbortSignal): Promise<SimilarityPage>;
  clear(queryId: string, signal: AbortSignal): Promise<void>;
  thumbnail(query: QueryReceipt, signal: AbortSignal): Promise<Blob>;
};
export function similarityGateway(workspace: string): SimilarityGateway {
  const workspaceId = uuid(workspace),
    path = `/api/workspaces/${workspaceId}/personas/photos/similarity`;
  const post = (route: string, body: unknown, signal: AbortSignal) =>
    apiClient.post<unknown>(`${path}/${route}`, body, {
      signal,
      credentials: "same-origin",
      mode: "same-origin",
      cache: "no-store",
      redirect: "error",
      retries: 0,
      timeoutMs: 85000,
    });
  return {
    workspaceId,
    ...readActions(post, path, workspaceId),
    ...queryActions(post, workspaceId),
  };
}

type Post = (
  route: string,
  body: unknown,
  signal: AbortSignal,
) => Promise<unknown>;
function readActions(
  post: Post,
  path: string,
  workspaceId: string,
): Pick<SimilarityGateway, "readiness" | "clear" | "thumbnail"> {
  return {
    async readiness(signal) {
      const r = object(await post("readiness", {}, signal), [
        "workspace_id",
        "state",
        "policy_id",
      ]);
      const result = {
        workspace_id: uuid(r.workspace_id),
        state: choice(r.state, [
          "processing_unavailable",
          "calibration_required",
          "calibration_expired",
          "ready",
        ]),
        policy_id: r.policy_id === null ? null : text(r.policy_id, 160),
      };
      requireContract(
        !signal.aborted &&
          result.workspace_id === workspaceId &&
          (result.state !== "ready" || result.policy_id !== null),
      );
      return result;
    },
    ...cleanupActions(post, path, workspaceId),
  };
}

function queryActions(
  post: Post,
  workspaceId: string,
): Pick<SimilarityGateway, "prepare" | "search"> {
  return {
    async prepare(command, signal) {
      const r = parseQueryReceipt(await post("prepare", command, signal));
      requireContract(
        !signal.aborted &&
          r.workspace_id === workspaceId &&
          r.query_id === command.request_id &&
          r.source_sha256 === command.sha256,
      );
      return r;
    },
    async search(command, signal) {
      const r = parseSimilarityPage(await post("search", command, signal));
      requireContract(
        !signal.aborted &&
          r.workspace_id === workspaceId &&
          r.query_id === command.query_id &&
          r.request_id === command.request_id &&
          r.face_index === command.face_index &&
          r.scope === command.scope,
      );
      return r;
    },
  };
}

function cleanupActions(
  post: Post,
  path: string,
  workspaceId: string,
): Pick<SimilarityGateway, "clear" | "thumbnail"> {
  return {
    async clear(queryId, signal) {
      const r = object(
        await post("clear", { query_id: uuid(queryId) }, signal),
        ["query_id", "workspace_id", "closed"],
      );
      requireContract(
        !signal.aborted &&
          uuid(r.query_id) === queryId &&
          uuid(r.workspace_id) === workspaceId &&
          r.closed === true,
      );
    },
    async thumbnail(query, signal) {
      requireContract(query.workspace_id === workspaceId);
      const blob = await fetchPrivatePng(
        `${path}/queries/${uuid(query.query_id)}/thumbnail`,
        signal,
      );
      requireContract(blob !== null);
      const bytes = new Uint8Array(
        await crypto.subtle.digest("SHA-256", await blob.arrayBuffer()),
      );
      requireContract(
        !signal.aborted &&
          Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("") ===
            query.thumbnail_sha256,
      );
      return blob;
    },
  };
}
