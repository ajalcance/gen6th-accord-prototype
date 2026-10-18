import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Home from "./console-test-studio";

beforeEach(() => {
  localStorage.clear();
  vi.useFakeTimers();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
});
function open() {
  render(<Home />);
  act(() => vi.advanceTimersByTime(0));
}
function click(name: string | RegExp) {
  fireEvent.click(screen.getByRole("button", { name }));
}

describe("console navigation and accessibility", () => {
  it("opens honest security readiness without claiming a breach assessment", () => {
    open();
    click("Connection & capabilities");
    const dialog = screen.getByRole("dialog", {
      name: "Connection & readiness",
    });
    expect(
      within(dialog).getByRole("region", { name: "Security readiness" }),
    ).toBeDefined();
    expect(within(dialog).getByText(/No breach assessment/)).toBeDefined();
    expect(screen.queryByText(/no breach detected/i)).toBeNull();
  });
  it("collapses and expands the sidebar without losing labelled navigation", () => {
    open();
    click("Collapse sidebar");
    expect(
      screen.getByRole("button", { name: "Expand sidebar", expanded: false }),
    ).toBeDefined();
    expect(
      screen.getByRole("complementary").classList.contains("is-collapsed"),
    ).toBe(true);
    click("Analysis & review");
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Analysis workspace",
      }),
    ).toBeDefined();
    click("Expand sidebar");
    expect(
      screen.getByRole("complementary").classList.contains("is-collapsed"),
    ).toBe(false);
  });
  it("keeps the console footer outside the scrolling workspace", () => {
    open();
    const footer = screen.getByRole("contentinfo");
    const main = screen.getByRole("main");
    expect(main.contains(footer)).toBe(false);
    expect(main.parentElement).toBe(footer.parentElement);
    click("Campaign approval");
    expect(screen.getByRole("contentinfo")).toBe(footer);
  });
  it("traps drawer focus, restores it on Escape and makes the background inert", () => {
    open();
    const trigger = screen.getByRole("button", { name: "Demo guide" });
    trigger.focus();
    fireEvent.click(trigger);
    const dialog = screen.getByRole("dialog", { name: "Demo guide" });
    const buttons = within(dialog).getAllByRole("button");
    expect(document.activeElement).toBe(buttons[0]);
    expect(document.querySelector(".studio")?.hasAttribute("inert")).toBe(true);
    expect(document.body.style.overflow).toBe("hidden");
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(buttons.at(-1));
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(buttons[0]);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(trigger);
    expect(document.body.style.overflow).toBe("");
  });
  it("opens quick actions by keyboard and reaches mobile utility modules", () => {
    open();
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    const dialog = screen.getByRole("dialog", { name: "Quick actions" });
    fireEvent.change(within(dialog).getByRole("searchbox"), {
      target: { value: "Connection" },
    });
    fireEvent.click(
      within(dialog).getByRole("button", { name: "Connection & readiness" }),
    );
    expect(
      screen.getByRole("dialog", { name: "Connection & readiness" }),
    ).toBeDefined();
    expect(screen.getByText("Persona API not connected")).toBeDefined();
    expect(screen.getByText("Local scan simulations")).toBeDefined();
  });
  it("shows a useful empty command state and navigates to a named fixture", () => {
    open();
    click(/Quick actions/);
    const dialog = screen.getByRole("dialog");
    fireEvent.change(within(dialog).getByRole("searchbox"), {
      target: { value: "No-such-screen" },
    });
    expect(within(dialog).getByRole("status").textContent).toContain(
      "No matching",
    );
    fireEvent.change(within(dialog).getByRole("searchbox"), {
      target: { value: "Iris" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: /Iris Sol/ }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(
      (screen.getByLabelText("Persona name") as HTMLInputElement).value,
    ).toBe("Iris Sol");
  });
  it("creates a separate blank persona and preserves the original draft", () => {
    open();
    click(/Start System Capture/);
    expect(
      (screen.getByLabelText("Persona name") as HTMLInputElement).value,
    ).toBe("");
    fireEvent.change(screen.getByLabelText("Persona name"), {
      target: { value: "Fictional Newcomer" },
    });
    click("Records");
    expect(
      screen.getByRole("heading", { name: "Fictional Newcomer" }),
    ).toBeDefined();
    click(/Nova Vale.*Review scenario/);
    click("System Capture");
    expect(
      (screen.getByLabelText("Persona name") as HTMLInputElement).value,
    ).toBe("Nova Vale");
    cleanup();
    open();
    click("Records");
    expect(
      screen.getByRole("heading", { name: "Fictional Newcomer" }),
    ).toBeDefined();
  });
});
describe("scan and assistant interactions", () => {
  it("advances real labelled stages and cancellation prevents ghost completion", () => {
    open();
    click("Analysis & review");
    click("Run demo scenario");
    act(() => vi.advanceTimersByTime(720));
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe(
      "1",
    );
    click("Cancel simulation");
    act(() => vi.advanceTimersByTime(4000));
    expect(screen.getByText(/Simulation cancelled/)).toBeDefined();
    expect(
      (
        screen.getByRole("button", {
          name: /Record demo review/,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    click("Retry demo");
    act(() => vi.advanceTimersByTime(3600));
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe(
      "5",
    );
  });
  it("explains evidence from a scripted source and applies a note only explicitly", () => {
    open();
    click("Analysis & review");
    click("Help draft a change request");
    const dialog = screen.getByRole("dialog", { name: "Demo guide" });
    expect(within(dialog).getByText(/scripted, source-linked/)).toBeDefined();
    expect(
      (
        screen.getByLabelText(
          "Comment anchored to evidence gap",
        ) as HTMLTextAreaElement
      ).value,
    ).toBe("");
    fireEvent.click(
      within(dialog).getByRole("button", { name: /Use as editable demo note/ }),
    );
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(
      (
        screen.getByLabelText(
          "Comment anchored to evidence gap",
        ) as HTMLTextAreaElement
      ).value,
    ).toContain("missing generation record");
    expect(
      (
        screen.getByRole("button", {
          name: /Record demo review/,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });
});
