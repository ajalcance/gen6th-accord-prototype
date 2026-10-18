import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PerformerCredits from "../app/passport/performer-credits";
import PerformerIdentity from "../app/passport/performer-identity";
import {
  creditGateway,
  type CreditProfile,
  type CreditTransport,
  type SaveCredits,
} from "../lib/persona-credits";
import { ApiError } from "../lib/api-client";
import {
  creditProfile,
  creditSnapshot,
  creditConfirmation,
} from "./credit-fixtures";
import {
  preparedSource,
  version,
  draftProvider,
} from "./prepared-write-fixtures";
import { GovernanceAccessLoss } from "../app/passport/saved-governance-read";

afterEach(cleanup);
function mountCredits(transport: CreditTransport, denied = vi.fn()) {
  const source = {
    ...preparedSource(),
    credits: creditGateway(version.workspace_id, transport),
  };
  const store = new Map();
  const element = draftProvider(
    store,
    <GovernanceAccessLoss.Provider value={denied}>
      <PerformerCredits source={source} version={version} denied={denied} />
    </GovernanceAccessLoss.Provider>,
  );
  return { ...render(element), element, source, store, denied };
}
it("shows persistent performer identity and attributed version source without a global trust badge", () => {
  render(<PerformerIdentity version={version} />);
  expect(
    screen.getByRole("region", { name: "Performer identity and attribution" })
      .textContent,
  ).toContain(version.persona_id);
  expect(screen.getByText(/Creator declared/)).toBeTruthy();
  expect(screen.queryByText("Verified performer")).toBeNull();
});
it("requires deliberate confirmation before saving aliases/credits and retries the same intent", async () => {
  const transport = vi
    .fn()
    .mockResolvedValue({ ...creditProfile, snapshot: null });
  mountCredits(transport);
  await screen.findByText(/No aliases or structured credits recorded/);
  fireEvent.click(
    screen.getByRole("button", { name: "Edit aliases & credits" }),
  );
  fireEvent.change(screen.getByLabelText("Other names"), {
    target: { value: "Nova" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Add contributor" }));
  fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Ari" } });
  const save = screen.getByRole("button", { name: "Record aliases & credits" });
  expect(save.hasAttribute("disabled")).toBe(true);
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I reviewed these aliases/ }),
  );
  transport.mockRejectedValueOnce(new ApiError("Unavailable", 503));
  fireEvent.click(save);
  transport.mockImplementation(async (path: string, body: SaveCredits) =>
    path === "read"
      ? { ...creditProfile, snapshot: null }
      : {
          ...creditSnapshot,
          request_id: body.request_id,
          content: body.content,
        },
  );
  fireEvent.click(
    await screen.findByRole("button", { name: "Retry same intent" }),
  );
  await waitFor(() =>
    expect(
      transport.mock.calls.filter(([path]) => path === "save"),
    ).toHaveLength(2),
  );
  const calls = transport.mock.calls.filter(([path]) => path === "save");
  expect(calls[0][1]).toEqual(calls[1][1]);
  await screen.findByText(/Storage receipt validated/);
  expect(calls[0][1]).toMatchObject({
    version_id: version.version_id,
    expected_previous_id: null,
    content: { aliases: ["Nova"], credits: [{ name: "Ari", actor_ref: null }] },
  });
});
it("only displays contributor confirmation from a bound server receipt and reloads it", async () => {
  let profile: CreditProfile = creditProfile;
  const transport = vi.fn(async (path: string) => {
    if (path === "read") return profile;
    profile = { ...creditProfile, confirmations: [creditConfirmation] };
    return creditConfirmation;
  });
  mountCredits(transport);
  await screen.findByText("Ari");
  expect(screen.queryByText("Contributor confirmed")).toBeNull();
  const form = screen
    .getByRole("button", { name: "Confirm my contribution" })
    .closest("form")!;
  fireEvent.click(within(form).getByRole("checkbox"));
  // Bind the synthetic reply to the newly authored request, as a real server must.
  transport.mockImplementation(async (path: string, body?: unknown) => {
    if (path === "read") return profile;
    const request_id = (body as { request_id: string }).request_id;
    const receipt = { ...creditConfirmation, request_id };
    profile = { ...creditProfile, confirmations: [receipt] };
    return receipt;
  });
  fireEvent.submit(form);
  await screen.findByText(/Storage receipt validated/);
  fireEvent.click(
    screen.getByRole("button", { name: "Reload credit receipts" }),
  );
  await screen.findByText("Contributor confirmed");
  expect(
    screen.queryByRole("button", { name: "Confirm my contribution" }),
  ).toBeNull();
});
it("failed and denied reads never appear as an empty or confirmed profile", async () => {
  const transport = vi.fn().mockRejectedValue(new ApiError("Unavailable", 503));
  const { denied } = mountCredits(transport);
  await screen.findByRole("alert");
  expect(screen.queryByText(/No aliases or structured credits/)).toBeNull();
  expect(
    screen.queryByRole("button", { name: "Edit aliases & credits" }),
  ).toBeNull();
  transport.mockRejectedValue(new ApiError("Denied", 403));
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  await waitFor(() => expect(denied).toHaveBeenCalledOnce());
});
it("rejects a claimed confirmation by another actor and retains exact retry recovery", async () => {
  const transport = vi
    .fn()
    .mockImplementation(async (path: string, body: { request_id: string }) =>
      path === "read"
        ? creditProfile
        : {
            ...creditConfirmation,
            request_id: body.request_id,
            actor_ref: "creator",
          },
    );
  mountCredits(transport);
  await screen.findByText("Ari");
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I confirm this credited role/ }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Confirm my contribution" }),
  );
  await screen.findByText(/response could not be validated/);
  expect(screen.queryByText("Contributor confirmed")).toBeNull();
  expect(
    screen.getByRole("button", { name: "Retry same intent" }),
  ).toBeTruthy();
});
