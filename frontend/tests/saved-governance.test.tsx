import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import SavedGallery from "../app/passport/saved-gallery";
import {
  SavedSourceContext,
  type SavedPersonaSource,
} from "../app/passport/saved-source";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import wire from "./fixtures/persona-wire.json";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});
const nextVersion = {
  ...wire.version,
  version_id: wire.save.request_id,
  revision: 2,
};
function source(
  transport: PersonaTransport,
  sessionKey = "test-session",
): SavedPersonaSource {
  return {
    workspaceId: wire.version.workspace_id,
    workspaceLabel: "Test workspace",
    sessionKey,
    gateway: personaGateway(wire.version.workspace_id, transport),
  };
}
function gallery(value: SavedPersonaSource) {
  return (
    <SavedSourceContext.Provider value={value}>
      <SavedGallery />
    </SavedSourceContext.Provider>
  );
}
function transport(): PersonaTransport {
  return async (operation, _workspace, command) => {
    if (operation === "gallery") return wire.gallery;
    if (operation === "load") return wire.version;
    if (operation === "versionHistory")
      return { items: [nextVersion, wire.version], next_before_revision: null };
    if (operation === "reviewHistory")
      return {
        items:
          (command as { version_id: string }).version_id ===
          wire.version.version_id
            ? [wire.review]
            : [],
        next_before_ordinal: null,
      };
    if (operation === "campaignOffers" || operation === "evidenceList")
      return { items: [], next_after_id: null };
    throw new Error("unexpected test operation");
  };
}
async function open() {
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  fireEvent.click(await screen.findByRole("button", { name: "Activity" }));
  await screen.findByRole("combobox", { name: "Saved version" });
}

it("binds all sections to selected server versions and clears historical reviews on switching", async () => {
  const send = vi.fn<PersonaTransport>(transport());
  render(gallery(source(send)));
  await open();
  expect(
    screen.getByRole("option", { name: "Version 2 · newer than loaded head" }),
  ).toBeDefined();
  fireEvent.click(screen.getByRole("button", { name: "Reviews" }));
  await screen.findByRole("heading", { name: "No independent review yet" });
  fireEvent.change(screen.getByRole("combobox", { name: "Saved version" }), {
    target: { value: wire.version.version_id },
  });
  fireEvent.click(screen.getByRole("button", { name: "Reviews" }));
  await screen.findByText(wire.review.statement);
  fireEvent.change(screen.getByRole("combobox", { name: "Saved version" }), {
    target: { value: nextVersion.version_id },
  });
  expect(screen.queryByText(wire.review.statement)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Campaigns" }));
  await screen.findByRole("heading", { name: "No campaigns on this page" });
  fireEvent.click(screen.getByRole("button", { name: "Evidence" }));
  await screen.findByRole("heading", { name: "No evidence on this page" });
  expect(
    send.mock.calls
      .filter(
        ([operation]) =>
          operation === "campaignOffers" || operation === "evidenceList",
      )
      .every(
        ([, , command]) =>
          (command as { version_id: string }).version_id ===
          nextVersion.version_id,
      ),
  ).toBe(true);
});

it("removes governance and late responses when the trusted session source changes", async () => {
  let finish!: (value: unknown) => void;
  const delayed = new Promise((done) => {
    finish = done;
  });
  const send = vi.fn<PersonaTransport>(
    (operation, workspace, command, signal) =>
      operation === "reviewHistory"
        ? delayed
        : transport()(operation, workspace, command, signal),
  );
  const { rerender } = render(gallery(source(send)));
  await open();
  fireEvent.change(screen.getByRole("combobox", { name: "Saved version" }), {
    target: { value: wire.version.version_id },
  });
  fireEvent.click(screen.getByRole("button", { name: "Reviews" }));
  await waitFor(() =>
    expect(
      send.mock.calls.some(([operation]) => operation === "reviewHistory"),
    ).toBe(true),
  );
  rerender(gallery(source(transport(), "replacement-session")));
  await screen.findByRole("button", { name: /Open record/ });
  await act(async () => finish(wire.reviewHistory));
  expect(screen.queryByText(wire.review.statement)).toBeNull();
  expect(
    screen.queryByRole("region", { name: "Saved governance records" }),
  ).toBeNull();
});

it("rejects a cross-persona discovery response before rendering governance history", async () => {
  const send: PersonaTransport = (operation, workspace, command, signal) =>
    operation === "versionHistory"
      ? Promise.resolve({
          items: [{ ...wire.version, persona_id: wire.campaign.id }],
          next_before_revision: null,
        })
      : transport()(operation, workspace, command, signal);
  render(gallery(source(send)));
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  fireEvent.click(await screen.findByRole("button", { name: "Activity" }));
  await screen.findByRole("alert");
  expect(screen.queryByRole("combobox", { name: "Saved version" })).toBeNull();
  expect(screen.queryByText(wire.review.statement)).toBeNull();
});
