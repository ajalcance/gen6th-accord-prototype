import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import PassportStudio from "../app/passport/studio";
import SavedGallery from "../app/passport/saved-gallery";
import {
  SavedSourceContext,
  type SavedPersonaSource,
} from "../app/passport/saved-source";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import { ApiError } from "../lib/api-client";
import wire from "./fixtures/persona-wire.json";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});

function source(
  transport: PersonaTransport,
  sessionKey = "synthetic-session",
): SavedPersonaSource {
  return {
    workspaceId: wire.version.workspace_id,
    workspaceLabel: "Synthetic test workspace",
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
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
describe("saved record read surfaces", () => {
  it("rejects a source labelled for a different workspace before loading", () => {
    const transport = vi.fn<PersonaTransport>();
    render(
      gallery({ ...source(transport), workspaceId: wire.version.persona_id }),
    );
    expect(screen.getByRole("alert")).toBeDefined();
    expect(transport).not.toHaveBeenCalled();
  });
  it("exposes the real connection prerequisite without fetching or mixing browser fixtures", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    render(<PassportStudio />);
    expect(
      screen.getByRole("region", { name: "Saved records connection" }),
    ).toBeDefined();
    expect(screen.queryByRole("heading", { name: "Nova Vale" })).toBeNull();
    expect(
      (
        screen.getByRole("button", {
          name: "New capture",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false);
    expect(fetch).not.toHaveBeenCalled();
    expect(
      screen.queryByRole("button", { name: "Browser fixtures" }),
    ).toBeNull();
  });
  it("loads stored fixtures and separate version details without portrait or permission claims", async () => {
    const transport = vi.fn<PersonaTransport>(async (operation) =>
      operation === "gallery" ? wire.gallery : wire.version,
    );
    render(gallery(source(transport)));
    const card = await screen.findByRole("button", { name: /Open record/ });
    expect(card.querySelector("svg[role='img']")).toBeNull();
    fireEvent.click(card);
    expect(
      await screen.findByRole("heading", { name: wire.version.content.name }),
    ).toBeDefined();
    expect(document.activeElement).toBe(
      screen.getByRole("heading", { name: wire.version.content.name }),
    );
    expect(
      screen.getByText(wire.version.content.human_contribution),
    ).toBeDefined();
    expect(
      screen.queryByRole("button", { name: /review|campaign|export/i }),
    ).toBeNull();
    expect(transport.mock.calls.map(([operation]) => operation)).toEqual([
      "gallery",
      "load",
    ]);
    fireEvent.click(
      screen.getByRole("button", { name: "Back to saved records" }),
    );
    await screen.findByRole("button", { name: /Open record/ });
    expect(transport.mock.calls.map(([operation]) => operation)).toEqual([
      "gallery",
      "load",
      "gallery",
    ]);
  });
  it("submits search explicitly and starts a fresh first page", async () => {
    const transport = vi.fn<PersonaTransport>(async () => wire.gallery);
    render(gallery(source(transport)));
    await screen.findByRole("button", { name: /Open record/ });
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: " Fictional " },
    });
    expect(transport).toHaveBeenCalledTimes(1);
    fireEvent.submit(screen.getByRole("search"));
    await waitFor(() => expect(transport).toHaveBeenCalledTimes(2));
    expect(transport.mock.calls[1][2]).toEqual({
      search: "Fictional",
      after_persona_id: null,
      limit: 20,
    });
  });
  it("uses the validated next cursor and clears the preceding page during loading", async () => {
    const versions = Array.from({ length: 20 }, (_, i) => ({
      ...wire.version,
      persona_id: `00000000-0000-4000-8000-${String(i + 1).padStart(12, "0")}`,
      content: { ...wire.version.content, name: `Synthetic ${i + 1}` },
    }));
    const next = deferred<unknown>();
    const transport = vi.fn<PersonaTransport>(
      async (_operation, _workspace, command) =>
        (command as { after_persona_id: string | null }).after_persona_id ===
        null
          ? {
              workspace_id: wire.version.workspace_id,
              items: versions,
              next_after_persona_id: versions[19].persona_id,
            }
          : next.promise,
    );
    render(gallery(source(transport)));
    fireEvent.click(
      (await screen.findAllByRole("button", { name: "Next page" }))[0],
    );
    expect(screen.queryByRole("heading", { name: "Synthetic 1" })).toBeNull();
    expect(screen.getByRole("button", { name: "Stop loading" })).toBeDefined();
    expect(transport.mock.calls[1][2]).toMatchObject({
      after_persona_id: versions[19].persona_id,
    });
    await act(async () =>
      next.resolve({
        workspace_id: wire.version.workspace_id,
        items: [],
        next_after_persona_id: null,
      }),
    );
    expect(
      await screen.findByRole("heading", { name: "No saved personas found" }),
    ).toBeDefined();
  });
  it("clears data when refresh loses permission and offers no retry loop", async () => {
    let permitted = true;
    const transport = vi.fn<PersonaTransport>(async () => {
      if (!permitted) throw new ApiError("private detail", 403);
      return wire.gallery;
    });
    render(gallery(source(transport)));
    await screen.findByRole("button", { name: /Open record/ });
    permitted = false;
    fireEvent.click(screen.getByRole("button", { name: "Refresh records" }));
    expect((await screen.findByRole("alert")).textContent).toContain("access");
    expect(
      screen.queryByRole("button", { name: /Open record|Try again/ }),
    ).toBeNull();
    expect(transport).toHaveBeenCalledTimes(2);
  });
  it("retries an unavailable page only when requested", async () => {
    let calls = 0;
    const transport = vi.fn<PersonaTransport>(async () => {
      if (++calls === 1) throw new ApiError("private detail", 503);
      return wire.gallery;
    });
    render(gallery(source(transport)));
    const retry = await screen.findByRole("button", { name: "Try again" });
    expect(calls).toBe(1);
    fireEvent.click(retry);
    await screen.findByRole("button", { name: /Open record/ });
    expect(calls).toBe(2);
  });
  it("cancels a request and ignores its late success", async () => {
    const waiting = deferred<unknown>();
    const transport = vi.fn<PersonaTransport>(async () => waiting.promise);
    render(gallery(source(transport)));
    fireEvent.click(
      await screen.findByRole("button", { name: "Stop loading" }),
    );
    expect(transport.mock.calls[0][3]?.aborted).toBe(true);
    await act(async () => waiting.resolve(wire.gallery));
    expect(screen.queryByRole("button", { name: /Open record/ })).toBeNull();
    expect(screen.getByRole("button", { name: "Try again" })).toBeDefined();
  });
  it("clears a previous session immediately and never applies its pending result", async () => {
    const old = deferred<unknown>();
    const earlier = source(async () => old.promise, "session-a");
    const later = source(
      async () => ({
        workspace_id: wire.version.workspace_id,
        items: [],
        next_after_persona_id: null,
      }),
      "session-b",
    );
    const view = render(gallery(earlier));
    view.rerender(gallery(later));
    await screen.findByRole("heading", { name: "No saved personas found" });
    await act(async () => old.resolve(wire.gallery));
    expect(screen.queryByRole("button", { name: /Open record/ })).toBeNull();
    expect(localStorage.length).toBe(0);
  });
});
