/** Advisory reviewer brief: same-origin, private, never retried; output is validated display text. */
import { apiClient } from "./api-client";
import {
  choice,
  integer,
  list,
  object,
  requireContract,
  text,
  timestamp,
  uuid,
} from "./persona-validation";

export type ReviewerBrief = {
  persona_id: string;
  version_id: string;
  revision: number;
  state: "brief" | "insufficient_information";
  summary: string;
  gaps: string[];
  questions: string[];
  model: string;
  model_revision: string;
  generated_at: string;
  notice: string;
};
export type AssistantGateway = {
  workspaceId: string;
  brief: (
    personaId: string,
    revision: number | null,
    signal: AbortSignal,
  ) => Promise<ReviewerBrief>;
};

/** Model output is shown as plain text: no markup, control characters or links. */
const UNSAFE = /[<>`]|https?:|www\./i;
function hasControl(value: string): boolean {
  return [...value].some((char) => {
    const code = char.codePointAt(0) ?? 0;
    return code < 32 || code === 127;
  });
}
function plain(value: unknown, max: number): string {
  const result = text(value, max);
  requireContract(!UNSAFE.test(result) && !hasControl(result));
  return result;
}
export function parseBrief(value: unknown): ReviewerBrief {
  const r = object(value, [
    "persona_id",
    "version_id",
    "revision",
    "state",
    "summary",
    "gaps",
    "questions",
    "model",
    "model_revision",
    "generated_at",
    "notice",
  ]);
  return {
    persona_id: uuid(r.persona_id),
    version_id: uuid(r.version_id),
    revision: integer(r.revision),
    state: choice(r.state, ["brief", "insufficient_information"] as const),
    summary: plain(r.summary, 450),
    gaps: list(r.gaps, (item) => plain(item, 160), 4),
    questions: list(r.questions, (item) => plain(item, 160), 4),
    model: text(r.model, 200),
    model_revision: text(r.model_revision, 160),
    generated_at: timestamp(r.generated_at),
    notice: text(r.notice, 400),
  };
}
export function assistantGateway(workspace: string): AssistantGateway {
  const workspaceId = uuid(workspace);
  return {
    workspaceId,
    async brief(personaId, revision, signal) {
      const persona = uuid(personaId);
      requireContract(!signal.aborted);
      requireContract(revision === null || integer(revision) === revision);
      const result = parseBrief(
        await apiClient.post<unknown>(
          `/api/workspaces/${workspaceId}/personas/assistant/brief`,
          { persona_id: persona, revision },
          {
            signal,
            credentials: "same-origin",
            mode: "same-origin",
            cache: "no-store",
            redirect: "error",
            retries: 0,
            timeoutMs: 60000,
          },
        ),
      );
      requireContract(!signal.aborted);
      requireContract(
        result.persona_id === persona &&
          (revision === null || result.revision === revision),
      );
      return result;
    },
  };
}
