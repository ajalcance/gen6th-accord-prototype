/** Review requests are internal saved handoffs, separate from independent decisions. */
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
export type ReviewRequestCommand = {
  request_id: string;
  version_id: string;
  investigation_id: string;
};
export type ReviewRequestReceipt = ReviewRequestCommand & {
  id: string;
  workspace_id: string;
  ordinal: number;
  requester_ref: string;
  requested_at: string;
  state: "requested";
};
export type ReviewRequestPage = {
  workspace_id: string;
  version_id: string;
  items: ReviewRequestReceipt[];
  next_before_ordinal: number | null;
};
export function parseReviewRequest(raw: unknown): ReviewRequestReceipt {
  const r = object(raw, [
    "request_id",
    "version_id",
    "investigation_id",
    "id",
    "workspace_id",
    "ordinal",
    "requester_ref",
    "requested_at",
    "state",
  ]);
  return {
    request_id: uuid(r.request_id),
    version_id: uuid(r.version_id),
    investigation_id: uuid(r.investigation_id),
    id: uuid(r.id),
    workspace_id: uuid(r.workspace_id),
    ordinal: integer(r.ordinal),
    requester_ref: text(r.requester_ref, 160),
    requested_at: timestamp(r.requested_at),
    state: choice(r.state, ["requested"]),
  };
}
export function parseReviewRequests(
  raw: unknown,
  workspace: string,
  version: string,
  before: number | null,
): ReviewRequestPage {
  const r = object(raw, [
    "workspace_id",
    "version_id",
    "items",
    "next_before_ordinal",
  ]);
  const p = {
    workspace_id: uuid(r.workspace_id),
    version_id: uuid(r.version_id),
    items: list(r.items, parseReviewRequest, 20),
    next_before_ordinal:
      r.next_before_ordinal === null ? null : integer(r.next_before_ordinal),
  };
  requireContract(
    p.workspace_id === workspace &&
      p.version_id === version &&
      new Set(p.items.map((row) => row.id)).size === p.items.length,
  );
  p.items.forEach((row, index) =>
    requireContract(
      row.workspace_id === workspace &&
        row.version_id === version &&
        (before === null || row.ordinal < before) &&
        (index === 0 || row.ordinal < p.items[index - 1].ordinal),
    ),
  );
  requireContract(
    p.next_before_ordinal === null ||
      (p.items.length === 20 &&
        p.next_before_ordinal === p.items.at(-1)?.ordinal),
  );
  return p;
}
type Post = (
  route: string,
  body: unknown,
  signal: AbortSignal,
) => Promise<unknown>;
export function reviewRequestActions(post: Post, workspace: string) {
  return {
    async requestReview(command: ReviewRequestCommand, signal: AbortSignal) {
      const r = parseReviewRequest(
        await post("review-requests/request", command, signal),
      );
      requireContract(
        !signal.aborted &&
          r.workspace_id === workspace &&
          r.version_id === command.version_id &&
          r.investigation_id === command.investigation_id &&
          r.request_id === command.request_id,
      );
      return r;
    },
    async reviewRequests(
      version: string,
      before: number | null,
      signal: AbortSignal,
    ) {
      const r = parseReviewRequests(
        await post(
          "review-requests/history",
          { version_id: uuid(version), before_ordinal: before },
          signal,
        ),
        workspace,
        version,
        before,
      );
      requireContract(!signal.aborted);
      return r;
    },
  };
}
