/** Additional two-runtime integration command; the standard Node-only gate stays unchanged. */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import SavedRecord from "../app/passport/saved-record";
import {
  personaGateway,
  PersonaDisconnectedError,
} from "../lib/persona-gateway";
import { personaPreparedReadTransport } from "../lib/persona-prepared-read-transport";
import { installBridge } from "./governance-asgi-helper";
import wire from "./fixtures/persona-wire.json";
import { parseSave } from "../lib/persona-commands";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});
function gateway() {
  return personaGateway(
    wire.version.workspace_id,
    personaPreparedReadTransport(),
  );
}
function saved() {
  return (
    <SavedRecord
      personaId={wire.version.persona_id}
      close={() => {}}
      source={{
        workspaceId: wire.version.workspace_id,
        workspaceLabel: "Synthetic test workspace",
        sessionKey: "test-only-session",
        gateway: gateway(),
      }}
    />
  );
}
async function openGovernance() {
  await screen.findByRole(
    "heading",
    { name: wire.version.content.name },
    { timeout: 5000 },
  );
  fireEvent.click(screen.getByRole("button", { name: "Activity" }));
  await screen.findByRole(
    "combobox",
    { name: "Saved version" },
    { timeout: 5000 },
  );
}

it("takes real ASGI DTOs through the HTTP client, typed gateway and all saved governance sections", async () => {
  const bridge = installBridge();
  render(saved());
  await openGovernance();
  fireEvent.click(screen.getByRole("button", { name: "Reviews" }));
  await screen.findByText(wire.review.statement, {}, { timeout: 5000 });
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect audit reference" }),
  );
  await screen.findByText("Audit pending", {}, { timeout: 5000 });
  fireEvent.click(screen.getByRole("button", { name: "Campaigns" }));
  await screen.findByText("Recorded scope eligible", {}, { timeout: 5000 });
  await screen.findByText(wire.decision.statement, {}, { timeout: 5000 });
  fireEvent.click(screen.getByRole("button", { name: "Evidence" }));
  await screen.findByRole(
    "heading",
    { name: "Quarantined" },
    { timeout: 5000 },
  );
  expect(screen.queryByRole("link", { name: /download/i })).toBeNull();
  for (const { body, options } of bridge.calls) {
    expect(body).not.toHaveProperty("actor_ref");
    expect(options).toMatchObject({
      method: "POST",
      credentials: "same-origin",
      mode: "same-origin",
      cache: "no-store",
      redirect: "error",
    });
  }
  expect(bridge.calls.map((call) => call.path.split("/personas")[1])).toEqual([
    "/versions/query",
    "/versions/history/query",
    "/reviews/history/query",
    "/workflow/evidence/query",
    "/campaigns/query",
    "/campaigns/status/query",
    "/campaigns/history/query",
    "/evidence/query",
  ]);
}, 20000);

it.each(["permission_lost", "session_lost"])(
  "clears the complete saved view on %s without touching drafts",
  async (mode) => {
    localStorage.setItem("synthetic-browser-draft", "Keep my unsaved work");
    installBridge((path) =>
      path.includes("/evidence/query") ? mode : "ready",
    );
    render(saved());
    await openGovernance();
    fireEvent.click(screen.getByRole("button", { name: "Evidence" }));
    await screen.findByRole("alert", {}, { timeout: 5000 });
    expect(
      screen.queryByRole("combobox", { name: "Saved version" }),
    ).toBeNull();
    expect(screen.queryByText(wire.version.content.biography)).toBeNull();
    expect(localStorage.getItem("synthetic-browser-draft")).toBe(
      "Keep my unsaved work",
    );
  },
  15000,
);

it("keeps writes disconnected and does not implicitly retry a failed governance POST", async () => {
  const bridge = installBridge(() => "unavailable");
  const client = gateway();
  await expect(
    client.governance.versions(wire.version.persona_id, {
      before_revision: null,
      limit: 20,
    }),
  ).rejects.toMatchObject({ status: 503 });
  expect(bridge.fetch).toHaveBeenCalledTimes(1);
  await expect(client.save(parseSave(wire.save))).rejects.toBeInstanceOf(
    PersonaDisconnectedError,
  );
  expect(bridge.fetch).toHaveBeenCalledTimes(1);
}, 10000);

it.each(["revoked", "expired"])(
  "shows %s as current blocked use while retaining decision history",
  async (mode) => {
    installBridge(() => mode);
    render(saved());
    await openGovernance();
    fireEvent.click(screen.getByRole("button", { name: "Campaigns" }));
    await screen.findByText(
      mode === "revoked" ? "Owner revoked permission" : "Time window expired",
      {},
      { timeout: 5000 },
    );
    expect(screen.getByText("Use blocked")).toBeDefined();
    expect(screen.queryByText("Fixture use eligible")).toBeNull();
    await screen.findByRole(
      "heading",
      { name: "Decision history" },
      { timeout: 5000 },
    );
  },
  15000,
);

it.each(["rejected", "expired"])(
  "shows %s evidence metadata without exposing private bytes",
  async (mode) => {
    installBridge(() => mode);
    render(saved());
    await openGovernance();
    fireEvent.click(screen.getByRole("button", { name: "Evidence" }));
    await screen.findByRole(
      "heading",
      { name: mode === "rejected" ? "Rejected" : "Expired" },
      { timeout: 5000 },
    );
    expect(
      screen.queryByRole("button", { name: /download|upload/i }),
    ).toBeNull();
  },
  15000,
);
