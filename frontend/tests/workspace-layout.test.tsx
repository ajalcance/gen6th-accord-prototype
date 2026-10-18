import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Home from "../app/page";
import PassportStudio from "../app/passport/studio";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import wire from "./fixtures/persona-wire.json";

beforeEach(() => localStorage.clear());
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("workspace records without sample workflows", () => {
  it("ignores historical sample storage and never fetches without a source", () => {
    localStorage.setItem(
      "accord-h1-console-v2",
      JSON.stringify({
        schema: 2,
        selected: 0,
        records: [
          {
            id: "nova",
            variant: 0,
            draft: {
              name: "Nova Vale",
              bio: "Sample",
              contribution: "Sample",
              disclosure: "Sample",
            },
          },
        ],
      }),
    );
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    render(<Home />);
    expect(
      screen.getByRole("region", { name: "Saved records connection" }),
    ).toBeDefined();
    expect(document.body.textContent).not.toMatch(
      /gallery|fixture|demo|stub|Nova Vale|Iris Sol|Arden Grey|North Studio/i,
    );
    expect(fetch).not.toHaveBeenCalled();
    expect(localStorage.getItem("accord-h1-console-v2")).toContain("Nova Vale");
    expect(
      (
        screen.getByRole("button", {
          name: "New capture",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false);
  });
  it("puts actions in the header, record tools on one row and readiness only in the footer", () => {
    render(<Home />);
    const main = screen.getByRole("main");
    const tools = within(main).getByLabelText("Record tools");
    expect(
      tools.contains(screen.getByRole("heading", { name: "Records" })),
    ).toBe(true);
    expect(tools.contains(screen.getByRole("searchbox"))).toBe(true);
    expect(
      tools.contains(screen.getByRole("group", { name: "Record display" })),
    ).toBe(true);
    expect(within(main).queryByText("What does a passport record?")).toBeNull();
    expect(screen.queryByText("Pending review")).toBeNull();
    expect(
      within(screen.getByRole("banner")).queryByText(/connected/i),
    ).toBeNull();
    expect(
      within(screen.getByRole("banner")).getByText(/Records/),
    ).toBeDefined();
    expect(screen.queryByText("Workspace records")).toBeNull();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(
      within(main).queryByRole("button", { name: /Connection|Monitoring/ }),
    ).toBeNull();
    expect(
      within(screen.getByRole("contentinfo")).getByRole("button", {
        name: "Connection & capabilities",
      }),
    ).toBeDefined();
    expect(
      screen
        .getByRole("banner")
        .contains(screen.getByRole("group", { name: "Workspace actions" })),
    ).toBe(true);
  });
  it("keeps guide focus, keyboard shortcuts and unavailable navigation honest", () => {
    render(<Home />);
    const guide = screen.getByRole("button", { name: "Help & guide" });
    guide.focus();
    fireEvent.click(guide);
    const dialog = screen.getByRole("dialog", { name: "Workspace guide" });
    expect(
      within(dialog).getByRole("heading", {
        name: "Review evidence and decisions",
      }),
    ).toBeDefined();
    expect(
      within(dialog).getByText("What does a passport record?"),
    ).toBeDefined();
    expect(document.querySelector(".studio")?.hasAttribute("inert")).toBe(true);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(document.activeElement).toBe(guide);
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    expect(
      within(screen.getByRole("dialog", { name: "Quick actions" })).getByRole(
        "button",
        { name: "Records" },
      ),
    ).toBeDefined();
    fireEvent.click(
      within(screen.getByRole("dialog", { name: "Quick actions" })).getByRole(
        "button",
        { name: "System Capture" },
      ),
    );
    expect(
      screen.getByRole("heading", {
        name: "System Capture",
      }),
    ).toBeDefined();
    expect(screen.getByRole("form", { name: "System Capture" })).toBeDefined();
    expect(document.body.textContent).not.toMatch(/fixture|demo|stub/i);
    fireEvent.click(screen.getByRole("button", { name: "Back to records" }));
    expect(screen.getByRole("heading", { name: "Records" })).toBeDefined();
  });
  it("switches the display of supplied saved records without inventing portraits or reviews", async () => {
    const transport = vi.fn<PersonaTransport>(async () => wire.gallery);
    render(
      <PassportStudio
        savedSource={{
          workspaceId: wire.version.workspace_id,
          workspaceLabel: "Test workspace",
          sessionKey: "synthetic-test-session",
          gateway: personaGateway(wire.version.workspace_id, transport),
        }}
      />,
    );
    await screen.findByRole("button", { name: /Open record/ });
    fireEvent.click(screen.getByRole("button", { name: "List view" }));
    expect(
      screen
        .getByRole("list", { name: "list of workspace personas" })
        .classList.contains("saved-list"),
    ).toBe(true);
    expect(transport).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(/Demo reviewed|Review scenario/)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Grid view" }));
    expect(
      screen
        .getByRole("list", { name: "grid of workspace personas" })
        .classList.contains("saved-list"),
    ).toBe(false);
  });
});
