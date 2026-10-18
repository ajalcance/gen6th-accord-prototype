/** Explicit same-origin analysis commands. No automatic retry or model activation. */
import { apiClient } from "./api-client";
import { reviewRequestActions } from "./persona-investigation-reviews";
import {
  parseInvestigation,
  parseInvestigationPage,
  type InvestigationCommand,
  type InvestigationResult,
  type InvestigationPage,
} from "./persona-investigation-contracts";
import {
  choice,
  object,
  requireContract,
  text,
  uuid,
} from "./persona-validation";

export type InvestigationGateway = ReturnType<typeof reviewRequestActions> & {
  workspaceId: string;
  readiness(signal: AbortSignal): Promise<"ready" | "processing_unavailable">;
  generate(
    command: InvestigationCommand,
    signal: AbortSignal,
  ): Promise<InvestigationResult>;
  history(
    version: string,
    before: number | null,
    signal: AbortSignal,
  ): Promise<InvestigationPage>;
};
export function investigationGateway(workspace: string): InvestigationGateway {
  const workspaceId = uuid(workspace);
  const post = (route: string, body: unknown, signal: AbortSignal) =>
    apiClient.post<unknown>(
      `/api/workspaces/${workspaceId}/personas/photos/investigations/${route}`,
      body,
      {
        signal,
        credentials: "same-origin",
        mode: "same-origin",
        cache: "no-store",
        redirect: "error",
        retries: 0,
        timeoutMs: 85000,
      },
    );
  return {
    workspaceId,
    ...reviewRequestActions(post, workspaceId),
    async readiness(signal) {
      const r = object(await post("readiness", {}, signal), [
        "workspace_id",
        "state",
      ]);
      requireContract(!signal.aborted && uuid(r.workspace_id) === workspaceId);
      return choice(r.state, ["ready", "processing_unavailable"]);
    },
    generate: (command, signal) => generate(post, workspaceId, command, signal),
    async history(version, before, signal) {
      const result = parseInvestigationPage(
        await post(
          "history",
          { version_id: uuid(version), before_ordinal: before },
          signal,
        ),
        workspaceId,
        version,
        before,
      );
      requireContract(!signal.aborted);
      return result;
    },
  };
}

type Post = (
  route: string,
  body: unknown,
  signal: AbortSignal,
) => Promise<unknown>;
async function generate(
  post: Post,
  workspace: string,
  command: InvestigationCommand,
  signal: AbortSignal,
) {
  const body = { ...command, source_note: text(command.source_note, 500) };
  const result = parseInvestigation(await post("generate", body, signal));
  requireContract(
    !signal.aborted &&
      result.workspace_id === workspace &&
      result.version_id === body.version_id &&
      result.portrait_id === body.portrait_id &&
      result.generation_id === body.generation_id &&
      result.request_id === body.request_id &&
      result.query.query_id === body.query_id &&
      result.search.face_index === body.face_index &&
      result.search.scope === body.scope &&
      result.source_note === body.source_note,
  );
  return result;
}
