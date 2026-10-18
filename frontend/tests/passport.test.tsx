import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
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
  if (name === "Act as recipient" || name === "Act as creator")
    fireEvent.click(
      screen.getByText("Demo controls · fictional party and time"),
    );
  if (name === "Simulate interruption")
    fireEvent.click(screen.getByText("Scenario controls"));
  fireEvent.click(screen.getByRole("button", { name }));
}
function review() {
  click("System Capture");
  click(/Save version & open analysis/);
  click("Run demo scenario");
  act(() => vi.advanceTimersByTime(3600));
  click(/Record demo review/);
}
function accept() {
  review();
  click("Create demo offer");
  click("Act as recipient");
  fireEvent.click(screen.getByRole("checkbox"));
  click(/Accept demo scope/);
}
describe("fictional passport journey", () => {
  it.each(["edit draft", "switch persona"])(
    "does not carry an old evidence note into a changed draft: %s",
    (action) => {
      open();
      click("Analysis & review");
      fireEvent.change(
        screen.getByLabelText("Comment anchored to evidence gap"),
        {
          target: { value: "Note for the previous fictional draft" },
        },
      );
      if (action === "edit draft") {
        click("System Capture");
        fireEvent.change(screen.getByLabelText("Biography"), {
          target: { value: "Changed draft" },
        });
      } else {
        click("Records");
        click(/Iris Sol/);
      }
      click("Public passport");
      click("Private preview");
      expect(
        screen.queryByText("Note for the previous fictional draft"),
      ).toBeNull();
      expect(screen.getByText("No reviewer comment yet.")).toBeDefined();
    },
  );
  it("invalidates prior decisions when the review statement changes", () => {
    open();
    accept();
    click("Analysis & review");
    fireEvent.change(
      screen.getByLabelText("Comment anchored to evidence gap"),
      {
        target: { value: "New fictional evidence gap" },
      },
    );
    click("Public passport");
    expect(screen.getByText("Review pending")).toBeDefined();
    expect(screen.getByText("Campaign acceptance pending")).toBeDefined();
    click("Campaign approval");
    expect((screen.getByRole("checkbox") as HTMLInputElement).checked).toBe(
      false,
    );
  });
  it("gates the illustration comparison until the scenario is ready", () => {
    open();
    click("Analysis & review");
    expect(
      (
        screen.getByRole("button", {
          name: /Inspect illustration evidence/,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    click("Run demo scenario");
    act(() => vi.advanceTimersByTime(3600));
    click(/Inspect illustration evidence/);
    expect(screen.getByRole("slider")).toBeDefined();
  });
  it("keeps the complete demo journey browser-only", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    open();
    accept();
    fireEvent.click(screen.getByText("What is required for verification?"));
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(
      screen.getByText(/no persona records are sent to the backend/),
    ).toBeDefined();
  });
  it.each(["Persona name", "Biography", "Human contribution", "AI disclosure"])(
    "blocks an incomplete draft even after sidebar navigation: %s",
    (field) => {
      open();
      click("System Capture");
      fireEvent.change(screen.getByLabelText(field), {
        target: { value: "   " },
      });
      expect(
        (
          screen.getByRole("button", {
            name: /Save version & open analysis/,
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(true);
      expect(
        screen.getByText(/Complete the name, biography and contribution/),
      ).toBeDefined();
      fireEvent.submit(screen.getByRole("form", { name: "System Capture" }));
      expect(screen.getByLabelText(field)).toBeDefined();
      click("Analysis & review");
      click("Run demo scenario");
      act(() => vi.advanceTimersByTime(3600));
      expect(
        (
          screen.getByRole("button", {
            name: /Record demo review/,
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(true);
    },
  );
  it("supports form submission for a complete fictional draft", () => {
    open();
    click("System Capture");
    fireEvent.submit(screen.getByRole("form", { name: "System Capture" }));
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Analysis workspace",
      }),
    ).toBeDefined();
  });
  it.each(["Analysis & review", "Campaign approval"])(
    "clears prior acceptance when requesting changes from %s",
    (step) => {
      open();
      accept();
      click(step);
      click("Request changes");
      click("Public passport");
      expect(
        screen.getByText(
          step === "Analysis & review"
            ? "Review pending"
            : "Demo review recorded",
        ),
      ).toBeDefined();
      expect(
        screen.getByText(
          step === "Campaign approval"
            ? "Campaign changes requested"
            : "Campaign acceptance pending",
        ),
      ).toBeDefined();
      expect(screen.queryByText("Campaign scope accepted in demo")).toBeNull();
    },
  );
  it.each(["Run demo scenario", "Simulate interruption"])(
    "invalidates decisions when analysis changes through %s",
    (action) => {
      open();
      accept();
      click("Analysis & review");
      click(action);
      click("Public passport");
      expect(screen.getByText("Review pending")).toBeDefined();
      expect(screen.getByText("Campaign acceptance pending")).toBeDefined();
    },
  );
  it("requires fresh campaign confirmation after recording another review", () => {
    open();
    accept();
    click("Analysis & review");
    click(/Record demo review/);
    expect((screen.getByRole("checkbox") as HTMLInputElement).checked).toBe(
      false,
    );
    expect(
      (
        screen.getByRole("button", {
          name: /Accept demo scope/,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    click("Public passport");
    expect(screen.getByText("Demo review recorded")).toBeDefined();
    expect(screen.getByText("Campaign acceptance pending")).toBeDefined();
  });
  it("moves keyboard focus to the destination heading on journey navigation", () => {
    open();
    click("System Capture");
    expect(document.activeElement).toBe(
      screen.getByRole("heading", {
        level: 1,
        name: "System Capture record",
      }),
    );
  });
  it("filters the records and opens the selected fixture", () => {
    open();
    click("Drafts");
    expect(
      screen.getByRole("button", { name: "Drafts", pressed: true }),
    ).toBeDefined();
    expect(screen.queryByRole("heading", { name: "Nova Vale" })).toBeNull();
    click(/Iris Sol/);
    expect(
      (screen.getByLabelText("Persona name") as HTMLInputElement).value,
    ).toBe("Iris Sol");
  });
  it("saves a bounded draft and restores it after a reload", () => {
    open();
    click("System Capture");
    fireEvent.change(screen.getByLabelText("Persona name"), {
      target: { value: "Fictional Mira" },
    });
    cleanup();
    open();
    click("System Capture");
    expect(
      (screen.getByLabelText("Persona name") as HTMLInputElement).value,
    ).toBe("Fictional Mira");
  });
  it("keeps acceptance disabled until review and explicit confirmation", () => {
    open();
    click("Campaign approval");
    fireEvent.click(screen.getByRole("checkbox"));
    expect(
      (
        screen.getByRole("button", {
          name: /Accept demo scope/,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    click("Records");
    review();
    expect(
      (
        screen.getByRole("button", {
          name: /Accept demo scope/,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    click("Create demo offer");
    click("Act as recipient");
    fireEvent.click(screen.getByRole("checkbox"));
    click(/Accept demo scope/);
    expect(screen.getByText("Campaign scope accepted in demo")).toBeDefined();
    click("System Capture");
    fireEvent.change(screen.getByLabelText("Biography"), {
      target: { value: "Changed" },
    });
    click("Campaign approval");
    expect(
      (
        screen.getByRole("button", {
          name: /Accept demo scope/,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });
  it("preserves drafts after simulated failure and supports retry/comparison", () => {
    open();
    click("System Capture");
    click(/Save version & open analysis/);
    click("Run demo scenario");
    click("Simulate interruption");
    act(() => vi.advanceTimersByTime(2000));
    expect(screen.getByText(/Simulated interruption/)).toBeDefined();
    click("Retry demo");
    act(() => vi.advanceTimersByTime(3600));
    click(/Inspect candidate/);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "70" } });
    expect((screen.getByRole("slider") as HTMLInputElement).value).toBe("70");
    click("Request changes");
    expect(
      (screen.getByLabelText("Persona name") as HTMLInputElement).value,
    ).toBe("Nova Vale");
  });
  it("excludes reviewer notes from the public view and refuses verification", () => {
    open();
    click("System Capture");
    click(/Save version & open analysis/);
    fireEvent.change(
      screen.getByLabelText("Comment anchored to evidence gap"),
      { target: { value: "Fictional private note" } },
    );
    click("Public passport");
    expect(screen.queryByText("Fictional private note")).toBeNull();
    click("Private preview");
    expect(screen.getByText("Fictional private note")).toBeDefined();
    fireEvent.click(screen.getByText("What is required for verification?"));
    expect(
      screen.getByText(/Unsigned fixture — verification unavailable/),
    ).toBeDefined();
  });
  it("recovers from malformed or unavailable local storage", () => {
    localStorage.setItem("accord-h1-draft", "invalid");
    open();
    click("System Capture");
    expect(screen.getByText(/Browser storage unavailable/)).toBeDefined();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("Unavailable");
    });
    fireEvent.change(screen.getByLabelText("Persona name"), {
      target: { value: "Still editable" },
    });
    expect(
      (screen.getByLabelText("Persona name") as HTMLInputElement).value,
    ).toBe("Still editable");
  });
});
