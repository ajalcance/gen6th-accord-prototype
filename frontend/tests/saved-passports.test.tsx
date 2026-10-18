import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import SavedPassports from "../app/passport/saved-passports";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import { preparedSource } from "./prepared-write-fixtures";
import {
  gatewayFixture,
  offer,
  packageFixture,
  status,
  version,
} from "./passport-fixtures";
import type { SignedPassport } from "../lib/persona-passport-contracts";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
const second = {
  ...offer,
  id: "00000000-0000-4000-8000-000000000096",
  scope: {
    ...offer.scope,
    name: "Second production",
    production: { ...offer.scope.production!, episode: "Episode 2" },
  },
};
function sourceFixture(transport?: PersonaTransport) {
  const source = preparedSource();
  source.passports = gatewayFixture();
  source.gateway = personaGateway(
    version.workspace_id,
    transport ??
      (async (operation, _workspace, command) => {
        if (operation === "campaignOffers")
          return { items: [offer, second], next_after_id: null };
        if (operation === "campaignStatus") {
          const receipt =
            (command as { campaign_id: string }).campaign_id === offer.id
              ? offer
              : second;
          return {
            ...status,
            receipt,
            latest_decision: {
              ...status.latest_decision!,
              campaign_id: receipt.id,
            },
          };
        }
        throw new Error("Unexpected synthetic passport query");
      }),
  );
  return source;
}
it("discovers exact-version production offers and binds current status before showing controls", async () => {
  const source = sourceFixture();
  render(<SavedPassports source={source} version={version} />);
  await screen.findByRole("heading", {
    name: "Fictional short film · Episode 1",
  });
  fireEvent.change(screen.getByLabelText("Production offer"), {
    target: { value: second.id },
  });
  await screen.findByRole("heading", {
    name: "Fictional short film · Episode 2",
  });
  expect(
    screen.queryByRole("heading", { name: "Fictional short film · Episode 1" }),
  ).toBeNull();
});
it("clears pending signed export on production changes and ignores late completion", async () => {
  const source = sourceFixture();
  let finish!: (packet: SignedPassport) => void;
  vi.mocked(source.passports!.export).mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  render(<SavedPassports source={source} version={version} />);
  await screen.findByRole("button", { name: "Prepare signed passport" });
  fireEvent.click(
    screen.getByRole("checkbox", { name: /Share this exact version/ }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Prepare signed passport" }),
  );
  fireEvent.change(screen.getByLabelText("Production offer"), {
    target: { value: second.id },
  });
  await screen.findByRole("heading", {
    name: "Fictional short film · Episode 2",
  });
  await act(async () => finish(packageFixture()));
  expect(
    screen.queryByRole("link", { name: "Download passport JSON" }),
  ).toBeNull();
});
it("rejects status from a different saved version and exposes no signing controls", async () => {
  const source = sourceFixture(async (operation) =>
    operation === "campaignOffers"
      ? { items: [offer], next_after_id: null }
      : { ...status, receipt: { ...offer, version_id: crypto.randomUUID() } },
  );
  render(<SavedPassports source={source} version={version} />);
  await screen.findByText(/response could not be validated/);
  expect(
    screen.queryByRole("button", { name: "Prepare signed passport" }),
  ).toBeNull();
});

it("separates private issuance, public approval and verification without issuing on navigation", async () => {
  const source = sourceFixture();
  render(<SavedPassports source={source} version={version} />);
  await screen.findByRole("button", { name: "Prepare signed passport" });
  expect(
    screen.queryByRole("button", { name: "Verify passport package" }),
  ).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Verify package" }));
  await screen.findByRole("button", { name: "Verify passport package" });
  expect(
    screen.queryByRole("button", { name: "Prepare signed passport" }),
  ).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Public sharing" }));
  expect(
    screen.getByText("Public sharing is unavailable on this connection."),
  ).toBeDefined();
  expect(source.passports!.export).not.toHaveBeenCalled();
  expect(source.passports!.verify).not.toHaveBeenCalled();
});
