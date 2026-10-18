import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PassportStudio from "../app/passport/studio";
import { ApiError } from "../lib/api-client";
import { investigationGateway } from "../lib/persona-investigations";
import { preparedSource, version } from "./prepared-write-fixtures";

afterEach(cleanup);
function failedHistorySource() {
  const source = preparedSource();
  const history = vi
    .fn()
    .mockRejectedValueOnce(new ApiError("Unavailable", 503))
    .mockResolvedValue({
      workspace_id: source.workspaceId,
      version_id: version.version_id,
      items: [],
      next_before_ordinal: null,
    });
  const requests = vi.fn().mockRejectedValue(new ApiError("Unavailable", 503));
  source.investigations = {
    ...investigationGateway(source.workspaceId),
    history,
    reviewRequests: requests,
  };
  return { source, history, requests };
}
async function choosePerformer() {
  fireEvent.click(
    within(
      screen.getByRole("navigation", { name: "Persona journey" }),
    ).getByRole("button", { name: "Analysis & review" }),
  );
  const picker = await screen.findByRole("region", {
    name: "Choose a performer",
  });
  expect(
    within(picker)
      .getByRole("searchbox", { name: "Performer name" })
      .getAttribute("placeholder"),
  ).toBe("Search by performer name…");
  fireEvent.click(
    await within(picker).findByRole("button", {
      name: `Open analysis for ${version.content.name}, version 1`,
    }),
  );
}
it("recovers a scoped analysis failure and loads review request history only in Independent review", async () => {
  const { source, history, requests } = failedHistorySource();
  render(<PassportStudio savedSource={source} />);
  await choosePerformer();
  const analysis = await screen.findByRole("region", {
    name: "Analysis workspace",
  });
  expect((await within(analysis).findByRole("alert")).textContent).toMatch(
    /Could not load investigation history/,
  );
  expect(requests).not.toHaveBeenCalled();
  expect(
    screen.queryByRole("region", {
      name: "Independent review request history",
    }),
  ).toBeNull();
  expect(
    screen.queryByRole("button", { name: "Older investigations" }),
  ).toBeNull();
  fireEvent.click(within(analysis).getByRole("button", { name: "Try again" }));
  await within(analysis).findByText(
    "No investigation findings for this exact version.",
  );
  expect(history.mock.calls[1].slice(0, 2)).toEqual([version.version_id, null]);
  expect(within(analysis).queryByRole("alert")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Independent review" }));
  const requestHistory = await screen.findByRole("region", {
    name: "Independent review request history",
  });
  expect(
    (await within(requestHistory).findByRole("alert")).textContent,
  ).toMatch(/Could not load review requests/);
  expect(requests).toHaveBeenCalledWith(
    version.version_id,
    null,
    expect.any(AbortSignal),
  );
  expect(
    screen.queryByRole("region", { name: "Analysis workspace" }),
  ).toBeNull();
  expect(
    screen.queryByRole("button", { name: "Older review requests" }),
  ).toBeNull();
});
