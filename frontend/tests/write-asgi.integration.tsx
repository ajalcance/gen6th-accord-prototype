/** Synthetic ASGI service stubs validate actual HTTP DTOs/client/parsers/UI. SQL is separate. */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it } from "vitest";
import { vi } from "vitest";
import { personaGateway } from "../lib/persona-gateway";
import { personaPreparedReadTransport } from "../lib/persona-prepared-read-transport";
import { personaPreparedWriteTransport } from "../lib/persona-prepared-write-transport";
import { parseVersion } from "../lib/persona-receipts";
import { parseCampaign } from "../lib/persona-campaign-receipts";
import PreparedWriteWorkspace from "../app/passport/prepared-write-workspace";
import RecordCreation from "../app/passport/record-creation";
import { SavedSourceContext } from "../app/passport/saved-source";
import SavedRecord from "../app/passport/saved-record";
import {
  WriteDraftContext,
  type WriteDraftStore,
} from "../app/passport/prepared-write-state";
import { installWriteBridge } from "./write-asgi-helper";
import { portraitGateway, scanPortrait } from "./portrait-fixtures";
import wire from "./fixtures/persona-wire.json";

beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:synthetic");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

it("creates a first persona version through the ASGI save route without client attribution", async () => {
  const bridge = installWriteBridge();
  render(
    <SavedSourceContext.Provider value={source()}>
      <WriteDraftContext.Provider value={new Map()}>
        <RecordCreation records={() => {}} />
      </WriteDraftContext.Provider>
    </SavedSourceContext.Provider>,
  );
  fill("Persona name", "Authored initial record");
  fill("Biography", "A supplied creative biography.");
  fill("Human contribution", "The author wrote the narrative.");
  fill("AI disclosure", "No AI was used.");
  await scanPortrait();
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: "I confirm these details and approve this portrait as the first reference.",
    }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Register persona" }));
  await screen.findByRole(
    "region",
    { name: "Saved System Capture receipt" },
    { timeout: 5000 },
  );
  expect(bridge.calls).toHaveLength(1);
  expect(bridge.calls[0].body).toMatchObject({
    persona_id: null,
    expected_revision: 0,
    photo: {
      action: "attach",
      upload_id: "00000000-0000-4000-8000-000000000090",
    },
  });
  expect(bridge.calls[0].body).not.toHaveProperty("actor_ref");
  expect(bridge.calls[0].options).toMatchObject({
    method: "POST",
    credentials: "same-origin",
    cache: "no-store",
    redirect: "error",
  });
}, 10000);
function source() {
  return {
    workspaceId: wire.version.workspace_id,
    workspaceLabel: "Synthetic ASGI workspace",
    sessionKey: "explicit-synthetic-session",
    photos: portraitGateway(wire.version.workspace_id),
    gateway: personaGateway(
      wire.version.workspace_id,
      personaPreparedReadTransport(),
    ),
    writeGateway: personaGateway(
      wire.version.workspace_id,
      personaPreparedWriteTransport(),
    ),
    assets: [
      {
        version_id: wire.version.version_id,
        assets: parseCampaign(wire.campaign).assets,
      },
    ],
  };
}
function workspace(store: WriteDraftStore = new Map()) {
  render(
    <WriteDraftContext.Provider value={store}>
      <PreparedWriteWorkspace
        source={source()}
        version={parseVersion(wire.version)}
        denied={() => {}}
      />
    </WriteDraftContext.Provider>,
  );
}
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
  fill("Saved draft name", "Synthetic saved fixture");
  fill("Saved draft biography", "My fixture biography.");
  fill("Saved draft contribution", "My human contribution.");
  fill("Saved draft AI disclosure", "Synthetic fixture only.");
  confirm();
}
async function submitted(label: string) {
  fireEvent.click(screen.getByRole("button", { name: label }));
  await screen.findByText(/Storage receipt validated/, {}, { timeout: 5000 });
}

it("passes version, independent review, offer and campaign decision through real ASGI DTOs to forms", async () => {
  const bridge = installWriteBridge();
  workspace();
  fillSave();
  await submitted("Save version");
  fireEvent.click(screen.getByRole("button", { name: "Independent review" }));
  await screen.findByLabelText(
    "Independent review statement",
    {},
    { timeout: 5000 },
  );
  fill("Review decision", "approved");
  fill("Independent review statement", "Reviewed exact synthetic version.");
  confirm();
  await submitted("Record review");
  fireEvent.click(screen.getByRole("button", { name: "Offer campaign" }));
  await screen.findByLabelText("Campaign name", {}, { timeout: 5000 });
  fill("Campaign name", "Synthetic scoped offer");
  fill("Named recipient", "recipient-a");
  fill("Campaign purpose", "Fixture editorial use.");
  fill("Campaign conditions", "No sublicensing.");
  fill("Starts at (include timezone)", "2026-10-04T04:00:00Z");
  fill("Ends at (include timezone)", "2026-10-05T04:00:00Z");
  fireEvent.click(
    screen.getByRole("checkbox", { name: wire.campaign.assets[0].label }),
  );
  confirm();
  await submitted("Record offer");
  fireEvent.click(screen.getByRole("button", { name: "Decide campaign" }));
  await screen.findByLabelText(
    "Campaign decision statement",
    {},
    { timeout: 5000 },
  );
  fill("Campaign decision", "revoked");
  fill("Campaign decision statement", "Owner revokes the fixture scope.");
  confirm();
  await submitted("Record campaign decision");
  const writes = bridge.calls.filter((call) =>
    /\/(save|record|offer|decide)$/.test(call.path),
  );
  expect(writes).toHaveLength(4);
  for (const call of writes) {
    expect(call.body).not.toHaveProperty("actor_ref");
    expect(call.options).toMatchObject({
      method: "POST",
      credentials: "same-origin",
      mode: "same-origin",
      cache: "no-store",
      redirect: "error",
    });
  }
}, 30000);

it("preserves an exact uncertain HTTP intent across navigation and later edits", async () => {
  const bridge = installWriteBridge((path, attempt) =>
    path.endsWith("/versions/save") && attempt === 1 ? "unavailable" : "ready",
  );
  workspace();
  fillSave();
  fireEvent.click(screen.getByRole("button", { name: "Save version" }));
  await screen.findByText(/outcome is uncertain/, {}, { timeout: 5000 });
  fill("Saved draft name", "Later unsaved work");
  fireEvent.click(screen.getByRole("button", { name: "Independent review" }));
  fireEvent.click(screen.getByRole("button", { name: "Edit version" }));
  await submitted("Retry same intent");
  const writes = bridge.calls.filter((call) =>
    call.path.endsWith("/versions/save"),
  );
  expect(writes).toHaveLength(2);
  expect(writes[0].body).toEqual(writes[1].body);
  expect(
    (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
  ).toBe("Later unsaved work");
}, 15000);

it.each(["session_lost", "permission_lost"])(
  "clears server content on write %s and keeps the authored draft",
  async (mode) => {
    installWriteBridge((path) =>
      path.endsWith("/versions/save") ? mode : "ready",
    );
    const store: WriteDraftStore = new Map();
    render(
      <WriteDraftContext.Provider value={store}>
        <SavedRecord
          source={source()}
          personaId={wire.version.persona_id}
          close={() => {}}
        />
      </WriteDraftContext.Provider>,
    );
    fireEvent.click(
      await screen.findByRole(
        "button",
        { name: "Edit persona" },
        { timeout: 5000 },
      ),
    );
    fillSave();
    fireEvent.click(screen.getByRole("button", { name: "Save version" }));
    await screen.findByText(/saved view was cleared/, {}, { timeout: 5000 });
    expect(screen.queryByText(wire.version.content.biography)).toBeNull();
    expect([...store.values()][0].fields.name).toBe("Synthetic saved fixture");
    expect([...store.values()][0].checkpoint?.state.phase).toBe("denied");
  },
  15000,
);

it("turns a real ASGI conflict into comparison without overwriting or silently retrying", async () => {
  const bridge = installWriteBridge((path) =>
    path.endsWith("/versions/save") ? "conflict" : "ready",
  );
  workspace();
  fillSave();
  fireEvent.click(screen.getByRole("button", { name: "Save version" }));
  await screen.findByText(/server record changed/, {}, { timeout: 5000 });
  fireEvent.click(
    screen.getByRole("button", { name: "Compare latest saved version" }),
  );
  await screen.findByRole(
    "heading",
    { name: "Latest saved version" },
    { timeout: 5000 },
  );
  expect(
    screen.queryByRole("button", { name: "Retry same intent" }),
  ).toBeNull();
  expect(
    bridge.calls.filter((call) => call.path.endsWith("/versions/save")),
  ).toHaveLength(1);
  expect(
    (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
  ).toBe("Synthetic saved fixture");
}, 15000);

it("retains an uncertain intent through denied retry and restored saved access", async () => {
  const bridge = installWriteBridge((path, attempt) => {
    if (!path.endsWith("/versions/save")) return "ready";
    return attempt === 1
      ? "unavailable"
      : attempt === 2
        ? "permission_lost"
        : "ready";
  });
  const store: WriteDraftStore = new Map();
  const record = (key: string) => (
    <WriteDraftContext.Provider value={store}>
      <SavedRecord
        key={key}
        source={source()}
        personaId={wire.version.persona_id}
        close={() => {}}
      />
    </WriteDraftContext.Provider>
  );
  const mounted = render(record("before-denial"));
  fireEvent.click(
    await screen.findByRole(
      "button",
      { name: "Edit persona" },
      { timeout: 5000 },
    ),
  );
  fillSave();
  fireEvent.click(screen.getByRole("button", { name: "Save version" }));
  await screen.findByText(/outcome is uncertain/, {}, { timeout: 5000 });
  fireEvent.click(screen.getByRole("button", { name: "Retry same intent" }));
  await screen.findByText(/saved view was cleared/, {}, { timeout: 5000 });
  expect([...store.values()][0].checkpoint?.uncertain).toBe(true);
  mounted.rerender(record("after-restoration"));
  fireEvent.click(
    await screen.findByRole(
      "button",
      { name: "Edit persona" },
      { timeout: 5000 },
    ),
  );
  expect(
    (
      screen.getByRole("button", {
        name: "Save version",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  await submitted("Retry same intent");
  const writes = bridge.calls.filter((call) =>
    call.path.endsWith("/versions/save"),
  );
  expect(writes).toHaveLength(3);
  expect(writes[0].body).toEqual(writes[2].body);
}, 20000);
