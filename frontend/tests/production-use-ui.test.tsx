import { cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { PersonaTransport } from "../lib/persona-gateway";
import {
  mountPrepared,
  preparedSource,
  receipt,
} from "./prepared-write-fixtures";
import { gatewayFixture, offer, version } from "./passport-fixtures";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}
async function openOffer() {
  fireEvent.click(screen.getByRole("button", { name: "Offer campaign" }));
  await screen.findByLabelText("Campaign name");
  for (const [label, value] of [
    ["Campaign name", "Fictional film"],
    ["Named recipient", offer.scope.recipient_ref],
    ["Campaign purpose", "Episode only."],
    ["Campaign conditions", "No advertising."],
    ["Starts at (include timezone)", "2026-10-02T04:00:00Z"],
    ["Ends at (include timezone)", "2026-10-03T04:00:00Z"],
  ])
    fill(label, value);
  fireEvent.click(
    screen.getByRole("checkbox", { name: offer.assets[0].label }),
  );
}
it("records a named production role with optional claims and exact approval/assets", async () => {
  const write = vi.fn<PersonaTransport>(async (operation, _workspace, body) =>
    receipt(operation, body),
  );
  mountPrepared(preparedSource(write));
  await openOffer();
  fireEvent.click(
    screen.getByRole("checkbox", { name: "Name a production and role" }),
  );
  const submit = screen.getByRole("button", {
    name: "Record offer",
  }) as HTMLButtonElement;
  expect(submit.disabled).toBe(true);
  for (const [label, value] of [
    ["Production title", "Fictional film"],
    ["Episode or named installment", "Episode 1"],
    ["Character or role name", "Captain North"],
    ["Permitted appearance and adaptation", "Costume change only."],
  ])
    fill(label, value);
  expect(screen.getByText(/Optional · up to 8/)).toBeDefined();
  expect(
    screen.getByRole("button", { name: "Choose supporting evidence" }),
  ).toBeDefined();
  fireEvent.click(screen.getByRole("checkbox", { name: /I authorize only/ }));
  fireEvent.click(submit);
  await screen.findByText(/Storage receipt validated/);
  expect(write.mock.calls[0][2]).toMatchObject({
    version_id: version.version_id,
    scope: {
      production: {
        title: "Fictional film",
        role_name: "Captain North",
        episode: "Episode 1",
        supporting_references: [],
      },
    },
  });
});
it("loads exact-version production assets explicitly without substituting private evidence", async () => {
  const source = preparedSource(),
    gateway = gatewayFixture();
  delete source.assets;
  source.passports = gateway;
  mountPrepared(source);
  fireEvent.click(screen.getByRole("button", { name: "Offer campaign" }));
  expect(gateway.assets).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Load production assets" }),
  );
  await screen.findByLabelText("Campaign name");
  expect(gateway.assets).toHaveBeenCalledWith(
    version.version_id,
    expect.any(AbortSignal),
  );
});
