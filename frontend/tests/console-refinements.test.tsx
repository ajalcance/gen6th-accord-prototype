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
function scenario() {
  click("Analysis & review");
  click("Run demo scenario");
  act(() => vi.advanceTimersByTime(3600));
}
function offer() {
  scenario();
  click(/Record demo review/);
  click("Create demo offer");
}

describe("task-focused console interactions", () => {
  it("turns queue metrics into filters and preserves results when switching views", () => {
    open();
    click(/NEEDS REVIEW/);
    expect(
      screen.getByRole("button", { name: "Needs review", pressed: true }),
    ).toBeDefined();
    expect(screen.queryByRole("heading", { name: "Iris Sol" })).toBeNull();
    click("List");
    expect(
      screen.getByRole("button", { name: "List", pressed: true }),
    ).toBeDefined();
    click(/Nova Vale.*Open review/);
    expect(
      screen.getByRole("heading", { level: 1, name: "Analysis workspace" }),
    ).toBeDefined();
    click("Records");
    click(/DEMO REVIEWS/);
    expect(screen.getByText("No matching personas")).toBeDefined();
    click("Clear filters");
    expect(screen.getByRole("heading", { name: "Iris Sol" })).toBeDefined();
  });
  it("offers campaign as the next action for a reviewed record", () => {
    open();
    scenario();
    click(/Record demo review/);
    click("Records");
    click("Reviewed");
    click(/Nova Vale.*Open campaign/);
    expect(
      screen.getByRole("heading", { level: 1, name: "Campaign approval" }),
    ).toBeDefined();
  });
  it("focuses command search, supports arrow navigation and reports unmatched utility searches", () => {
    open();
    click("Quick actions");
    const search = within(screen.getByRole("dialog")).getByRole("searchbox");
    expect(document.activeElement).toBe(search);
    fireEvent.change(search, { target: { value: "Connection" } });
    fireEvent.keyDown(search, { key: "ArrowDown" });
    expect(document.activeElement).toBe(
      within(screen.getByRole("dialog")).getByRole("button", {
        name: "Connection & readiness",
      }),
    );
    fireEvent.change(search, { target: { value: "activity nonexistent" } });
    expect(screen.getByRole("status").textContent).toContain("No matching");
  });
  it("navigates a guide source to its actual System Capture workspace", () => {
    open();
    click("Demo guide");
    click("What is missing before review?");
    click(/System Capture record · evidence-gap/);
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByRole("form", { name: "System Capture" })).toBeDefined();
  });
  it("filters actual tab activity without inventing version snapshots", () => {
    open();
    scenario();
    click("Activity & versions");
    fireEvent.change(screen.getByLabelText("Filter activity"), {
      target: { value: "campaign" },
    });
    expect(
      within(screen.getByRole("dialog")).getByRole("status").textContent,
    ).toContain("No matching activity");
    fireEvent.change(screen.getByLabelText("Filter activity"), {
      target: { value: "analysis" },
    });
    expect(screen.getByText("Fixture analysis started")).toBeDefined();
    const summaries = screen.getByRole("dialog").querySelectorAll("summary");
    const last = summaries[summaries.length - 1] as HTMLElement;
    last.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "Close panel" }),
    );
  });
  it("associates System Capture hints and exposes supplied evidence without an upload affordance", () => {
    open();
    click("System Capture");
    for (const name of [
      "Persona name",
      "Biography",
      "Human contribution",
      "AI disclosure",
    ]) {
      const input = screen.getByLabelText(name);
      expect(
        document.getElementById(input.getAttribute("aria-describedby") ?? "")
          ?.textContent,
      ).toBeTruthy();
    }
    expect(screen.queryByRole("button", { name: /uploads/i })).toBeNull();
    fireEvent.click(screen.getByText("Inspect supplied illustration"));
    expect(
      screen.getByText(/Presence is not a verified rights claim/),
    ).toBeDefined();
  });
  it("shows the selected reference and opens unrelated evidence inline", () => {
    open();
    scenario();
    click(/Inspect candidate/);
    expect(
      screen.getByRole("button", { name: /Close comparison/, expanded: true }),
    ).toBeDefined();
    fireEvent.click(screen.getByText("Unrelated control · inspect reference"));
    expect(screen.getByText(/geometric-control-01/)).toBeDefined();
    expect(screen.queryByRole("dialog")).toBeNull();
  });
  it("uses pointer position for comparison and clamps beyond either image edge", () => {
    open();
    scenario();
    click(/Inspect candidate/);
    const canvas = screen
      .getByRole("region", { name: "Palette comparison" })
      .querySelector(".compare-images") as HTMLDivElement;
    vi.spyOn(canvas, "getBoundingClientRect").mockReturnValue({
      left: 100,
      width: 200,
    } as DOMRect);
    canvas.setPointerCapture = vi.fn();
    canvas.hasPointerCapture = vi.fn(() => true);
    canvas.releasePointerCapture = vi.fn();
    function pointer(type: string, x: number) {
      const event = new Event(type, { bubbles: true });
      Object.defineProperties(event, {
        clientX: { value: x },
        button: { value: 0 },
        pointerId: { value: 1 },
      });
      fireEvent(canvas, event);
    }
    pointer("pointerdown", 250);
    expect((screen.getByRole("slider") as HTMLInputElement).value).toBe("75");
    pointer("pointermove", 500);
    expect((screen.getByRole("slider") as HTMLInputElement).value).toBe("100");
    pointer("pointermove", 50);
    expect((screen.getByRole("slider") as HTMLInputElement).value).toBe("0");
    pointer("pointerup", 50);
    expect(canvas.releasePointerCapture).toHaveBeenCalledWith(1);
  });
  it("requires explicit revocation confirmation and permits cancellation", () => {
    open();
    offer();
    click("Revoke demo offer");
    expect(screen.queryByText("Offer revoked")).toBeNull();
    expect(
      screen.getByText(/Nova Vale · fixture-v1 · Solstice Goods/),
    ).toBeDefined();
    click("Keep offer");
    expect(
      screen.queryByRole("button", { name: "Confirm revocation" }),
    ).toBeNull();
    click("Revoke demo offer");
    click("Confirm revocation");
    expect(screen.getByText("Offer revoked")).toBeDefined();
    expect(
      screen.queryByRole("button", { name: "Revoke demo offer" }),
    ).toBeNull();
  });
  it("discards revocation confirmation when the scope changes", () => {
    open();
    offer();
    click("Revoke demo offer");
    fireEvent.change(screen.getByLabelText("Campaign purpose"), {
      target: { value: "New scope" },
    });
    expect(
      screen.queryByRole("button", { name: "Confirm revocation" }),
    ).toBeNull();
    click("Create demo offer");
    expect(
      screen.queryByRole("button", { name: "Confirm revocation" }),
    ).toBeNull();
  });
  it("shows accepted state instead of a repeated acceptance action", () => {
    open();
    offer();
    fireEvent.click(
      screen.getByText("Demo controls · fictional party and time"),
    );
    click("Act as recipient");
    fireEvent.click(screen.getByRole("checkbox"));
    click(/Accept demo scope/);
    click("Campaign approval");
    expect(
      screen.queryByRole("button", { name: /Accept demo scope/ }),
    ).toBeNull();
    expect(screen.getByText(/Scope accepted in this demo/)).toBeDefined();
  });
  it("keeps private notes out of inspected public fields in either preview mode", () => {
    open();
    click("Analysis & review");
    fireEvent.change(
      screen.getByLabelText("Comment anchored to evidence gap"),
      { target: { value: "Private fixture note" } },
    );
    click("Public passport");
    click("Private preview");
    expect(
      screen.getByRole("button", { name: "Private preview", pressed: true }),
    ).toBeDefined();
    fireEvent.click(screen.getByText("Review export fields"));
    expect(
      screen.getByRole("region", { name: "Unsigned export" }).textContent,
    ).not.toContain("Private fixture note");
    expect(
      screen.queryByRole("button", { name: "Inspect verification state" }),
    ).toBeNull();
    click("Public preview");
    expect(screen.queryByText("Private fixture note")).toBeNull();
  });
});
