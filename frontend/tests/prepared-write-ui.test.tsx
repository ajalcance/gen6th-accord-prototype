import { cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api-client";
import type { PersonaTransport } from "../lib/persona-gateway";
import { personaGateway } from "../lib/persona-gateway";
import {
  mountPrepared,
  preparedSource,
  receipt,
  version,
  campaign,
} from "./prepared-write-fixtures";
import wire from "./fixtures/persona-wire.json";

afterEach(cleanup);
function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}
function confirm() {
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: /I have reviewed|I reviewed|I authorize/,
    }),
  );
}
function fillSave() {
  fill("Saved draft name", "Local draft");
  fill("Saved draft biography", "My draft biography.");
  fill("Saved draft contribution", "My human contribution.");
  fill("Saved draft AI disclosure", "Synthetic fixture.");
  confirm();
}
async function success() {
  await screen.findByText(/Storage receipt validated/);
}

describe("prepared structured write forms", () => {
  it("requires explicit confirmation and saves against the loaded head without changing the draft", async () => {
    const write = vi.fn<PersonaTransport>(async (operation, _workspace, body) =>
      receipt(operation, body),
    );
    mountPrepared(preparedSource(write));
    const submit = screen.getByRole("button", {
      name: "Save version",
    }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);
    fillSave();
    expect(submit.disabled).toBe(false);
    fill("Saved draft name", "Edited draft");
    expect(submit.disabled).toBe(true);
    fireEvent.submit(submit.closest("form")!);
    expect(write).not.toHaveBeenCalled();
    confirm();
    fireEvent.click(submit);
    await success();
    expect(write.mock.calls[0][2]).toMatchObject({
      persona_id: version.persona_id,
      expected_revision: version.revision,
      content: { name: "Edited draft" },
    });
    expect(
      (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
    ).toBe("Edited draft");
  });
  it("records independent review using the fetched previous decision", async () => {
    const write = vi.fn<PersonaTransport>(async (operation, _workspace, body) =>
      receipt(operation, body),
    );
    mountPrepared(preparedSource(write));
    fireEvent.click(screen.getByRole("button", { name: "Independent review" }));
    await screen.findByLabelText("Independent review statement");
    fill("Independent review statement", "I request more supporting evidence.");
    confirm();
    fireEvent.click(screen.getByRole("button", { name: "Record review" }));
    await success();
    expect(write.mock.calls[0][2]).toMatchObject({
      version_id: version.version_id,
      expected_previous_id: wire.review.id,
      decision: "changes_requested",
    });
  });
  it("offers only explicitly selected version-bound catalogue assets with the current approval", async () => {
    const write = vi.fn<PersonaTransport>(async (operation, _workspace, body) =>
      receipt(operation, body),
    );
    mountPrepared(preparedSource(write));
    fireEvent.click(screen.getByRole("button", { name: "Offer campaign" }));
    await screen.findByLabelText("Campaign name");
    fill("Campaign name", "Fixture campaign offer");
    fill("Named recipient", campaign.scope.recipient_ref);
    fill("Campaign purpose", "Editorial fixture use.");
    fill("Campaign conditions", "No sublicensing.");
    fill("Starts at (include timezone)", "2026-10-04T04:00:00Z");
    fill("Ends at (include timezone)", "2026-10-05T04:00:00Z");
    fireEvent.click(
      screen.getByRole("checkbox", { name: campaign.assets[0].label }),
    );
    confirm();
    fireEvent.click(screen.getByRole("button", { name: "Record offer" }));
    await success();
    expect(write.mock.calls[0][2]).toMatchObject({
      version_id: version.version_id,
      review_id: wire.review.id,
      scope: {
        asset_ids: [campaign.assets[0].id],
        recipient_ref: campaign.scope.recipient_ref,
      },
    });
  });
  it.each(["accepted", "changes_requested", "revoked"])(
    "records explicit %s with the discovered campaign and previous decision",
    async (decision) => {
      const write = vi.fn<PersonaTransport>(
        async (operation, _workspace, body) => receipt(operation, body),
      );
      mountPrepared(preparedSource(write));
      fireEvent.click(screen.getByRole("button", { name: "Decide campaign" }));
      await screen.findByLabelText("Campaign decision statement");
      fill("Campaign decision", decision);
      fill("Campaign decision statement", "My explicit fixture decision.");
      confirm();
      fireEvent.click(
        screen.getByRole("button", {
          name: "Record campaign decision",
        }),
      );
      await success();
      expect(write.mock.calls[0][2]).toMatchObject({
        campaign_id: campaign.id,
        expected_previous_id: wire.decision.id,
        decision,
      });
    },
  );
  it.each(["missing", "foreign", "duplicate", "invalid"])(
    "refuses an %s asset catalogue without substituting evidence",
    async (mode) => {
      const source = preparedSource();
      if (mode === "missing") delete source.assets;
      if (mode === "foreign")
        source.assets = [
          {
            version_id: "00000000-0000-4000-8000-000000000099",
            assets: campaign.assets,
          },
        ];
      if (mode === "duplicate")
        source.assets = [source.assets![0], source.assets![0]];
      if (mode === "invalid")
        source.assets![0].assets = [
          { ...campaign.assets[0], digest: "invalid" },
        ];
      mountPrepared(source);
      fireEvent.click(screen.getByRole("button", { name: "Offer campaign" }));
      expect(
        screen.getByRole("heading", {
          name: "Production asset catalogue",
        }),
      ).toBeDefined();
      expect(screen.queryByRole("button", { name: "Record offer" })).toBeNull();
    },
  );
  it("keeps actions absent without explicit injection and refuses a foreign write workspace", () => {
    const source = preparedSource();
    delete source.writeGateway;
    const mounted = mountPrepared(source);
    expect(
      screen.queryByRole("navigation", { name: "Prepared action" }),
    ).toBeNull();
    mounted.rerender(
      mounted.element({
        ...source,
        writeGateway: personaGateway("00000000-0000-4000-8000-000000000099"),
      }),
    );
    expect(screen.getByRole("alert").textContent).toMatch(
      /could not be validated/,
    );
  });
  it("blocks offers when the latest independent review requests changes", async () => {
    const source = preparedSource();
    source.gateway = personaGateway(version.workspace_id, async () => ({
      items: [{ ...wire.review, decision: "changes_requested" }],
      next_before_ordinal: null,
    }));
    mountPrepared(source);
    fireEvent.click(screen.getByRole("button", { name: "Offer campaign" }));
    await screen.findByText(/current independent approval/);
    expect(screen.queryByRole("button", { name: "Record offer" })).toBeNull();
  });
  it("preserves input and sends no replacement success on malformed receipts", async () => {
    mountPrepared(preparedSource(async () => ({ private: "Invalid" })));
    fillSave();
    fireEvent.click(screen.getByRole("button", { name: "Save version" }));
    await screen.findByText(/response could not be validated/);
    expect(screen.queryByText(/Storage receipt validated/)).toBeNull();
    expect(
      (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
    ).toBe("Local draft");
  });
  it("retains an identical uncertain intent across pane navigation and later draft edits", async () => {
    const write = vi
      .fn<PersonaTransport>()
      .mockRejectedValueOnce(new ApiError("unavailable", 503))
      .mockImplementation(async (operation, _workspace, body) =>
        receipt(operation, body),
      );
    const mounted = mountPrepared(preparedSource(write));
    fillSave();
    fireEvent.click(screen.getByRole("button", { name: "Save version" }));
    await screen.findByText(/outcome is uncertain/);
    fill("Saved draft name", "Later unsaved edit");
    fireEvent.submit(
      screen.getByLabelText("Saved draft name").closest("form")!,
    );
    expect(write).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Independent review" }));
    fireEvent.click(screen.getByRole("button", { name: "Edit version" }));
    expect(
      (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
    ).toBe("Later unsaved edit");
    fireEvent.click(screen.getByRole("button", { name: "Retry same intent" }));
    await success();
    expect(write.mock.calls[0][2]).toEqual(write.mock.calls[1][2]);
    expect(
      [...mounted.store.values()].every((entry) => !entry.checkpoint),
    ).toBe(true);
  });
});
