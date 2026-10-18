import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import ProductionHistory from "../app/passport/production-history";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import { ApiError } from "../lib/api-client";
import { campaign, version } from "./prepared-write-fixtures";

afterEach(cleanup);
it("shows scoped production proposals without certifying an appearance or fetching permission before expansion", async () => {
  const transport = vi.fn<PersonaTransport>(async (operation) => {
    if (operation === "campaignOffers")
      return { items: [campaign], next_after_id: null };
    throw new ApiError("Unavailable", 503);
  });
  render(
    <ProductionHistory
      gateway={personaGateway(version.workspace_id, transport)}
      version={version}
    />,
  );
  await screen.findByText("Offer recorded");
  expect(
    transport.mock.calls.every(([operation]) => operation === "campaignOffers"),
  ).toBe(true);
  expect(
    screen.getByText(/does not prove the performer appeared/),
  ).toBeTruthy();
  const details = screen
    .getByText("Inspect current permission, assets & decision history")
    .closest("details")!;
  details.open = true;
  fireEvent(details, new Event("toggle", { bubbles: true }));
  await waitFor(() =>
    expect(
      transport.mock.calls.some(
        ([operation]) => operation === "campaignStatus",
      ),
    ).toBe(true),
  );
});
it("keeps failed history distinct from an empty page", async () => {
  const transport = vi
    .fn<PersonaTransport>()
    .mockRejectedValue(new ApiError("Unavailable", 503));
  render(
    <ProductionHistory
      gateway={personaGateway(version.workspace_id, transport)}
      version={version}
    />,
  );
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Could not load production history",
  );
  expect(
    screen.queryByText("No production proposals on this page."),
  ).toBeNull();
});
