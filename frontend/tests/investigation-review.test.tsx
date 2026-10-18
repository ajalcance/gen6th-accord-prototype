import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import RequestInvestigationReview, {
  InvestigationReviewRequests,
} from "../app/passport/investigation-review-request";
import {
  parseReviewRequest,
  parseReviewRequests,
} from "../lib/persona-investigation-reviews";
import { investigationGateway } from "../lib/persona-investigations";
import { apiClient, ApiError } from "../lib/api-client";
import { preparedSource } from "./prepared-write-fixtures";
import { investigationResult } from "./investigation-fixtures";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function receipt() {
  const packet = investigationResult();
  return {
    id: crypto.randomUUID(),
    request_id: crypto.randomUUID(),
    version_id: packet.version_id,
    investigation_id: packet.id,
    workspace_id: packet.workspace_id,
    ordinal: 1,
    requester_ref: "synthetic-human",
    requested_at: new Date().toISOString(),
    state: "requested" as const,
  };
}
it("rejects browser approval and mixed-version history receipts", () => {
  const row = receipt();
  expect(parseReviewRequest(row)).toEqual(row);
  expect(() => parseReviewRequest({ ...row, state: "approved" })).toThrow();
  expect(() =>
    parseReviewRequests(
      {
        workspace_id: row.workspace_id,
        version_id: row.version_id,
        items: [row, row],
        next_before_ordinal: null,
      },
      row.workspace_id,
      row.version_id,
      null,
    ),
  ).toThrow();
});
it("uses private explicit request/history transport with exact evidence binding", async () => {
  const row = receipt(),
    post = vi.spyOn(apiClient, "post").mockResolvedValue(row);
  const gateway = investigationGateway(row.workspace_id),
    signal = new AbortController().signal;
  const c = {
    request_id: row.request_id,
    version_id: row.version_id,
    investigation_id: row.investigation_id,
  };
  expect(await gateway.requestReview(c, signal)).toEqual(row);
  post.mockResolvedValue({
    workspace_id: row.workspace_id,
    version_id: row.version_id,
    items: [row],
    next_before_ordinal: null,
  });
  await gateway.reviewRequests(row.version_id, null, signal);
  expect(
    post.mock.calls.every(
      (call) => call[2]?.retries === 0 && call[2]?.cache === "no-store",
    ),
  ).toBe(true);
  post.mockResolvedValue({ ...row, investigation_id: crypto.randomUUID() });
  await expect(gateway.requestReview(c, signal)).rejects.toThrow();
});
it("saves an internal request only on click and retries the same evidence intent", async () => {
  const source = preparedSource(),
    packet = investigationResult(),
    row = receipt();
  const request = vi
    .fn()
    .mockRejectedValueOnce(new ApiError("Unavailable", 503))
    .mockResolvedValue(row);
  source.investigations = {
    ...investigationGateway(source.workspaceId),
    requestReview: request,
  };
  render(
    <RequestInvestigationReview
      source={source}
      packet={packet}
      denied={vi.fn()}
    />,
  );
  expect(request).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Request independent review" }),
  );
  fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
  await screen.findByText(/Review requested/);
  expect(request.mock.calls[1][0]).toEqual(request.mock.calls[0][0]);
  expect(request.mock.calls[0][0]).toMatchObject({
    version_id: packet.version_id,
    investigation_id: packet.id,
  });
});
it("loads exact-version request history and clears on permission loss", async () => {
  const source = preparedSource(),
    row = receipt(),
    denied = vi.fn();
  const history = vi
    .fn()
    .mockResolvedValueOnce({
      workspace_id: row.workspace_id,
      version_id: row.version_id,
      items: [row],
      next_before_ordinal: null,
    })
    .mockRejectedValue(new ApiError("Denied", 403));
  source.investigations = {
    ...investigationGateway(source.workspaceId),
    reviewRequests: history,
  };
  render(
    <InvestigationReviewRequests
      source={source}
      version={row.version_id}
      denied={denied}
    />,
  );
  await screen.findByText(/Requested by synthetic-human/);
  fireEvent.click(
    screen.getByRole("button", { name: "Refresh review requests" }),
  );
  await waitFor(() => expect(denied).toHaveBeenCalled());
  expect(screen.queryByText(/Requested by synthetic-human/)).toBeNull();
  expect(history).toHaveBeenCalledWith(
    row.version_id,
    null,
    expect.any(AbortSignal),
  );
});
