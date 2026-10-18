import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import GovernanceRecovery from "./legacy-passport/governance-recovery";
import PassportStudio from "./legacy-passport-studio";
import { initialConsole } from "./legacy-passport/console-fixtures";
import type { Draft } from "./legacy-passport/fixture-data";

const draft: Draft = {
  name: "Preserved fictional draft",
  bio: "Fictional biography",
  contribution: "Hand edited composition",
  disclosure: "No AI model ran",
};
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});
function click(name: string | RegExp) {
  fireEvent.click(screen.getByRole("button", { name }));
}
function setup() {
  const close = vi.fn(),
    connection = vi.fn();
  render(
    <GovernanceRecovery draft={draft} close={close} connection={connection} />,
  );
  return { close, connection };
}
function scenario(value: string) {
  fireEvent.change(screen.getByLabelText("Recovery example"), {
    target: { value },
  });
}

describe("draft-preserving recovery interactions", () => {
  it("compares conflict snapshots without overwrite or automatic retry", async () => {
    const { close } = setup();
    click("Run recovery example");
    expect((await screen.findByRole("alert")).textContent).toContain(
      "server record changed",
    );
    expect(
      screen.queryByRole("button", { name: "Retry same example request" }),
    ).toBeNull();
    click("Compare latest example version");
    expect(
      await screen.findByRole("heading", { name: "Your preserved draft" }),
    ).toBeDefined();
    expect(
      screen.getByRole("heading", { name: "Latest fictional version" }),
    ).toBeDefined();
    expect(screen.getAllByText(draft.name).length).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /merge|overwrite/i }),
    ).toBeNull();
    click("Keep draft & close");
    expect(close).toHaveBeenCalledOnce();
  });
  it("explicitly retries an uncertain outcome with the same request and content", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    setup();
    scenario("unavailable");
    click("Run recovery example");
    expect((await screen.findByRole("alert")).textContent).toContain(
      "outcome is uncertain",
    );
    const request =
      screen.getByText("Request ID").nextElementSibling?.textContent;
    click("Retry same example request");
    expect(
      await screen.findByRole("heading", { name: "Example retry resolved" }),
    ).toBeDefined();
    expect(screen.getByText("Request ID").nextElementSibling?.textContent).toBe(
      request,
    );
    expect(screen.getByText(/No real save occurred/)).toBeDefined();
    expect(fetch).not.toHaveBeenCalled();
  });
  it("offers connection recovery after permission loss without a fallback login or retry", async () => {
    const { connection } = setup();
    scenario("denied");
    click("Run recovery example");
    expect((await screen.findByRole("alert")).textContent).toContain(
      "permission",
    );
    expect(screen.getByText(/No fallback login/)).toBeDefined();
    expect(screen.queryByRole("button", { name: /retry/i })).toBeNull();
    click("Connection details");
    expect(connection).toHaveBeenCalledOnce();
  });
  it("keeps cancellation uncertain and permits the same intent retry", async () => {
    setup();
    scenario("unavailable");
    click("Run recovery example");
    click("Stop waiting");
    expect((await screen.findByRole("alert")).textContent).toContain(
      "may have committed",
    );
    click("Retry same example request");
    expect(
      await screen.findByRole("heading", { name: "Example retry resolved" }),
    ).toBeDefined();
  });
  it("discards late results when switching scenarios", async () => {
    setup();
    scenario("unavailable");
    click("Run recovery example");
    scenario("denied");
    click("Run recovery example");
    expect((await screen.findByRole("alert")).textContent).toContain(
      "permission",
    );
    expect(screen.queryByText(/outcome is uncertain/)).toBeNull();
  });
  it("requires all System Capture fields before running a recovery example", () => {
    render(
      <GovernanceRecovery
        draft={{ ...draft, disclosure: "" }}
        close={vi.fn()}
        connection={vi.fn()}
      />,
    );
    expect(
      (
        screen.getByRole("button", {
          name: "Run recovery example",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(
      screen.getByText(/Complete the four System Capture fields/),
    ).toBeDefined();
  });
  it("preserves edited form fields and the local revision across conflict and panel dismissal", async () => {
    render(<PassportStudio initialState={initialConsole()} />);
    click("System Capture");
    fireEvent.change(screen.getByLabelText("Persona name"), {
      target: { value: draft.name },
    });
    click("Evidence & decisions");
    click("Save recovery");
    click("Run recovery example");
    await screen.findByRole("alert");
    click("Compare latest example version");
    await screen.findByRole("heading", { name: "Your preserved draft" });
    click("Keep draft & close");
    expect(
      (screen.getByLabelText("Persona name") as HTMLInputElement).value,
    ).toBe(draft.name);
    expect(screen.getByText(/fixture-v1/).textContent).toContain(
      "draft edited",
    );
  });
});
