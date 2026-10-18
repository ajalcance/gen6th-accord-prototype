/** Same-origin lifecycle transport; receipts must bind the exact intent and workspace. */
import { apiClient } from "./api-client";
import {
  parseAppendLifecycle,
  parseLifecycleReceipt,
  type AppendLifecycle,
} from "./persona-lifecycle-contracts";
import {
  parseLifecyclePage,
  parseLifecycleProfile,
} from "./persona-lifecycle-reads";
import { integer, requireContract, uuid } from "./persona-validation";

type Transport = (
  path: string,
  body: unknown,
  signal: AbortSignal,
) => Promise<unknown>;
function scopedPost(workspace: string, transport?: Transport) {
  return async (path: string, body: unknown, signal: AbortSignal) => {
    if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
    const raw = await (transport
      ? transport(path, body, signal)
      : apiClient.post(
          `/api/workspaces/${workspace}/personas/lifecycle/${path}`,
          body,
          {
            signal,
            credentials: "same-origin",
            cache: "no-store",
            mode: "same-origin",
            redirect: "error",
            retries: 0,
          },
        ));
    if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
    return raw;
  };
}
export function lifecycleGateway(workspaceId: string, transport?: Transport) {
  const workspace = uuid(workspaceId),
    post = scopedPost(workspace, transport);
  return {
    workspaceId: workspace,
    async read(version: string, signal: AbortSignal) {
      const id = uuid(version),
        result = parseLifecycleProfile(
          await post("read", { version_id: id }, signal),
        );
      requireContract(
        result.workspace_id === workspace && result.version_id === id,
      );
      return result;
    },
    async append(command: AppendLifecycle, signal: AbortSignal) {
      const body = parseAppendLifecycle(command),
        result = parseLifecycleReceipt(await post("append", body, signal));
      requireContract(
        result.workspace_id === workspace &&
          result.version_id === body.version_id &&
          result.request_id === body.request_id &&
          result.expected_previous_id === body.expected_previous_id &&
          result.id !== body.expected_previous_id &&
          JSON.stringify(result.content) === JSON.stringify(body.content),
      );
      return result;
    },
    async history(version: string, before: number | null, signal: AbortSignal) {
      const id = uuid(version),
        cursor = before === null ? null : integer(before);
      const result = parseLifecyclePage(
        await post(
          "history",
          { version_id: id, before_ordinal: cursor },
          signal,
        ),
      );
      requireContract(
        result.workspace_id === workspace &&
          result.version_id === id &&
          result.items.every((v) => cursor === null || v.ordinal < cursor),
      );
      return result;
    },
  };
}
export type LifecycleGateway = ReturnType<typeof lifecycleGateway>;
