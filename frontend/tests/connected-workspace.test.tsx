import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import ConnectedWorkspace, {
  sessionSource,
} from "../app/passport/connected-workspace";

const workspace = "00000000-0000-4000-8000-000000000001";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("keeps the unconfigured workspace empty without making requests", () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  render(<ConnectedWorkspace enabled={false} />);
  expect(fetch).not.toHaveBeenCalled();
  expect(screen.queryByRole("button", { name: "Sign in" })).toBeNull();
});

it("binds records to a verified session and clears them before signing out", async () => {
  const fetch = vi.fn<typeof globalThis.fetch>(
    async (path) =>
      new Response(
        JSON.stringify(
          String(path).endsWith("/session")
            ? {
                workspace_id: workspace,
                session_key: "verified-session",
                workspace_label: "Connected workspace",
              }
            : String(path).endsWith("/logout")
              ? { signed_out: true }
              : { items: [], next_before: null },
        ),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
  );
  vi.stubGlobal("fetch", fetch);
  render(<ConnectedWorkspace enabled />);
  fireEvent.click(await screen.findByRole("button", { name: "Account" }));
  fireEvent.click(await screen.findByRole("button", { name: "Sign out" }));
  await screen.findByRole("button", { name: "Sign in" });
  await waitFor(() =>
    expect(
      fetch.mock.calls.some(([path]) => String(path).endsWith("/logout")),
    ).toBe(true),
  );
  const options = fetch.mock.calls[0][1] as RequestInit;
  expect(options.credentials).toBe("same-origin");
  expect(options.cache).toBe("no-store");
});

it("refuses identity DTOs with extra authority or missing workspace context", () => {
  const valid = {
    workspace_id: workspace,
    session_key: "session",
    workspace_label: "Workspace",
  };
  expect(() => sessionSource({ ...valid, role: "creator" })).toThrow();
  expect(() => sessionSource({ ...valid, workspace_id: "wrong" })).toThrow();
  expect(() => sessionSource({ ...valid, session_key: "" })).toThrow();
});
