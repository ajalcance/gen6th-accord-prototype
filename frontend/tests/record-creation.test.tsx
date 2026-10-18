import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { portraitGateway, scanPortrait } from "./portrait-fixtures";
import PassportStudio from "../app/passport/studio";
import type { SavedPersonaSource } from "../app/passport/saved-source";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import { ApiError } from "../lib/api-client";
import type { SaveCommand } from "../lib/persona-contracts";
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

function receipt(command: unknown) {
  const intent = command as SaveCommand;
  return { ...wire.version, revision: 1, content: intent.content };
}
function source(write: PersonaTransport): SavedPersonaSource {
  const workspaceId = wire.version.workspace_id;
  return {
    workspaceId,
    workspaceLabel: "System Capture test workspace",
    sessionKey: "creation-test-session",
    gateway: personaGateway(workspaceId, async () => wire.gallery),
    writeGateway: personaGateway(workspaceId, write),
    photos: portraitGateway(workspaceId),
  };
}
function openCreation() {
  fireEvent.click(screen.getByRole("button", { name: "New capture" }));
}
async function fill(name = "Authored persona") {
  for (const [label, value] of [
    ["Persona name", name],
    ["Biography", "My authored biography."],
    ["Human contribution", "I wrote and directed this persona."],
    ["AI disclosure", "No AI was used."],
  ]) {
    fireEvent.change(screen.getByLabelText(label), { target: { value } });
  }
  await scanPortrait();
}
function confirm() {
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I confirm these details/ }),
  );
}
function save() {
  fireEvent.click(screen.getByRole("button", { name: "Register persona" }));
}
function disabled() {
  return (
    screen.getByRole("button", {
      name: "Register persona",
    }) as HTMLButtonElement
  ).disabled;
}
function name() {
  return (screen.getByLabelText("Persona name") as HTMLInputElement).value;
}
async function saved() {
  await screen.findByRole("region", { name: "Saved System Capture receipt" });
}

it("opens an empty editable draft without a connection, sends nothing and retains it across navigation", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  render(<PassportStudio />);
  openCreation();
  await fill();
  confirm();
  expect(disabled()).toBe(true);
  fireEvent.submit(screen.getByRole("form", { name: "System Capture" }));
  fireEvent.click(screen.getByRole("button", { name: "Back to records" }));
  openCreation();
  expect(name()).toBe("Authored persona");
  expect((screen.getByRole("checkbox") as HTMLInputElement).checked).toBe(
    false,
  );
  expect(document.body.textContent).not.toMatch(/demo|fixture|stub/i);
  expect(fetch).not.toHaveBeenCalled();
});

it("normalizes the initial intent and shows only a validated version-one receipt", async () => {
  const write = vi.fn<PersonaTransport>(
    async (_operation, _workspace, command) => receipt(command),
  );
  render(<PassportStudio savedSource={source(write)} />);
  openCreation();
  await fill("  Authored persona  ");
  expect(disabled()).toBe(true);
  confirm();
  save();
  await saved();
  expect(write).toHaveBeenCalledTimes(1);
  const command = write.mock.calls[0][2] as SaveCommand;
  expect(command).toMatchObject({
    persona_id: null,
    expected_revision: 0,
    content: { name: "Authored persona" },
  });
  expect(command.request_id).toMatch(/^[0-9a-f-]{36}$/);
  expect(Object.keys(command).sort()).toEqual([
    "content",
    "expected_revision",
    "persona_id",
    "photo",
    "request_id",
  ]);
  expect(
    within(
      screen.getByRole("region", { name: "Saved System Capture receipt" }),
    ).getByText(wire.version.persona_id),
  ).toBeDefined();
  const completion = screen.getByRole("heading", {
    name: "System Capture saved",
  });
  await waitFor(() => expect(document.activeElement).toBe(completion));
  expect(screen.queryByRole("form", { name: "System Capture" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Register persona" })).toBeNull();
  expect(screen.queryByLabelText("Persona name")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Back to records" }));
  openCreation();
  expect(
    screen.getByRole("heading", { name: "System Capture already saved" }),
  ).toBeDefined();
  expect(
    screen.queryByRole("region", { name: "Saved System Capture receipt" }),
  ).toBeNull();
  expect(screen.queryByRole("form", { name: "System Capture" })).toBeNull();
  expect(write).toHaveBeenCalledTimes(1);
  fireEvent.click(
    screen.getByRole("button", {
      name: "Start another System Capture",
    }),
  );
  expect(name()).toBe("");
  await fill("Second authored persona");
  confirm();
  save();
  await saved();
  expect(write).toHaveBeenCalledTimes(2);
  expect((write.mock.calls[1][2] as SaveCommand).request_id).not.toBe(
    command.request_id,
  );
});

it("requires new confirmation after editing and respects backend Unicode limits", async () => {
  render(
    <PassportStudio savedSource={source(async (_a, _b, c) => receipt(c))} />,
  );
  openCreation();
  await fill("😀".repeat(80));
  confirm();
  expect(disabled()).toBe(false);
  fireEvent.change(screen.getByLabelText("Persona name"), {
    target: { value: "a".repeat(81) },
  });
  expect(disabled()).toBe(true);
  expect(
    screen.getByLabelText("Persona name").getAttribute("aria-invalid"),
  ).toBe("true");
  expect(screen.getByText("Use at most 80 characters.")).toBeDefined();
  fireEvent.change(screen.getByLabelText("Persona name"), {
    target: { value: "   " },
  });
  confirm();
  expect(disabled()).toBe(true);
});

it("does not submit twice while a request is pending", async () => {
  let finish: (value: unknown) => void = () => {};
  const write = vi.fn<PersonaTransport>(
    async () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  render(<PassportStudio savedSource={source(write)} />);
  openCreation();
  await fill();
  confirm();
  save();
  fireEvent.submit(screen.getByRole("form", { name: "System Capture" }));
  expect(write).toHaveBeenCalledTimes(1);
  expect(disabled()).toBe(true);
  await act(async () => finish(receipt(write.mock.calls[0][2])));
  await saved();
});

it("retains an uncertain initial intent across navigation and retries the exact content after later edits", async () => {
  const write = vi.fn<PersonaTransport>(async (_a, _b, command) => {
    if (write.mock.calls.length === 1)
      throw new ApiError("Unavailable", 503, "HTTP_ERROR");
    return receipt(command);
  });
  render(<PassportStudio savedSource={source(write)} />);
  openCreation();
  await fill();
  confirm();
  save();
  await screen.findByText(/The outcome is uncertain/);
  fireEvent.change(screen.getByLabelText("Persona name"), {
    target: { value: "Later edits" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Back to records" }));
  openCreation();
  expect(disabled()).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Retry same intent" }));
  await saved();
  expect(write.mock.calls[0][2]).toEqual(write.mock.calls[1][2]);
  expect(screen.queryByLabelText("Persona name")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "View retained draft" }));
  expect(name()).toBe("Later edits");
  expect(
    (
      screen
        .getByLabelText("Persona name")
        .closest("fieldset") as HTMLFieldSetElement
    ).disabled,
  ).toBe(true);
  expect(screen.getByText(/Your fields include later edits/)).toBeDefined();
});

it("opens the saved record through a fresh authorized read from the completion screen", async () => {
  const write = vi.fn<PersonaTransport>(async (_a, _b, command) =>
    receipt(command),
  );
  const read = vi.fn<PersonaTransport>(async (operation) =>
    operation === "gallery" ? wire.gallery : receipt(write.mock.calls[0][2]),
  );
  const connected = source(write);
  connected.gateway = personaGateway(connected.workspaceId, read);
  render(<PassportStudio savedSource={connected} />);
  openCreation();
  await fill();
  confirm();
  save();
  await saved();
  const details = screen
    .getByText("Inspect storage receipt")
    .closest("details")!;
  expect(details.open).toBe(false);
  fireEvent.click(screen.getByRole("button", { name: "Open saved record" }));
  await screen.findByRole("heading", { name: "Authored persona" });
  expect(
    screen.getByRole("heading", { name: "Performer profile" }),
  ).toBeDefined();
  expect(
    read.mock.calls.find(([operation]) => operation === "load")?.[2],
  ).toEqual({ persona_id: wire.version.persona_id, revision: null });
  expect(write).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Records" }));
  expect(await screen.findByRole("heading", { name: "Records" })).toBeDefined();
  expect(
    screen.queryByRole("heading", { name: "Performer profile" }),
  ).toBeNull();
  expect(
    read.mock.calls.filter(([operation]) => operation === "load"),
  ).toHaveLength(1);
});

it.each([401, 403])(
  "retains authored input and blocks saving after access denial %s",
  async (status) => {
    const write = vi.fn<PersonaTransport>(async () => {
      throw new ApiError("Denied", status, "HTTP_ERROR");
    });
    render(<PassportStudio savedSource={source(write)} />);
    openCreation();
    await fill();
    confirm();
    save();
    await screen.findByText(/Access was denied/);
    expect(name()).toBe("Authored persona");
    expect(disabled()).toBe(true);
    expect(
      screen.queryByRole("region", { name: "Saved System Capture receipt" }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Retry same intent" }),
    ).toBeNull();
    fireEvent.submit(screen.getByRole("form", { name: "System Capture" }));
    expect(write).toHaveBeenCalledTimes(1);
  },
);

it("hides the prior session's draft and late receipt while retaining its exact unresolved request", async () => {
  let finish: (value: unknown) => void = () => {};
  const write = vi.fn<PersonaTransport>(
    async () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const original = source(write);
  const mounted = render(<PassportStudio savedSource={original} />);
  openCreation();
  await fill();
  confirm();
  save();
  mounted.rerender(<PassportStudio savedSource={null} />);
  expect(name()).toBe("");
  expect(disabled()).toBe(true);
  await act(async () => finish(receipt(write.mock.calls[0][2])));
  expect(
    screen.queryByRole("region", { name: "Saved System Capture receipt" }),
  ).toBeNull();
  mounted.rerender(
    <PassportStudio
      savedSource={{ ...original, sessionKey: "different-human-session" }}
    />,
  );
  expect(name()).toBe("");
  mounted.rerender(<PassportStudio savedSource={original} />);
  expect(name()).toBe("Authored persona");
  expect(disabled()).toBe(true);
  expect(
    screen.getByRole("button", { name: "Retry same intent" }),
  ).toBeDefined();
});

it("fails closed when the write gateway belongs to another workspace", async () => {
  const write = vi.fn<PersonaTransport>();
  render(
    <PassportStudio
      savedSource={{
        ...source(write),
        writeGateway: personaGateway(crypto.randomUUID(), write),
      }}
    />,
  );
  openCreation();
  await fill();
  confirm();
  expect(disabled()).toBe(true);
  save();
  expect(write).not.toHaveBeenCalled();
});

it("treats a malformed receipt as uncertain and permits only the same intent retry", async () => {
  const write = vi.fn<PersonaTransport>(async () => ({ invalid: true }));
  render(<PassportStudio savedSource={source(write)} />);
  openCreation();
  await fill();
  confirm();
  save();
  await screen.findByText(/response could not be validated/);
  expect(
    screen.queryByRole("region", { name: "Saved System Capture receipt" }),
  ).toBeNull();
  expect(disabled()).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Retry same intent" }));
  await waitFor(() => expect(write).toHaveBeenCalledTimes(2));
  expect(write.mock.calls[0][2]).toEqual(write.mock.calls[1][2]);
});

it("requires explicit conflict review and fresh confirmation before a new create intent", async () => {
  const write = vi.fn<PersonaTransport>(async () => {
    throw new ApiError("Conflict", 409, "HTTP_ERROR");
  });
  render(<PassportStudio savedSource={source(write)} />);
  openCreation();
  await fill();
  confirm();
  save();
  await screen.findByRole("button", {
    name: "I checked Records; prepare a new request",
  });
  expect(disabled()).toBe(true);
  expect(write).toHaveBeenCalledTimes(1);
  fireEvent.click(
    screen.getByRole("button", {
      name: "I checked Records; prepare a new request",
    }),
  );
  expect(disabled()).toBe(true);
  expect(name()).toBe("Authored persona");
  confirm();
  expect(disabled()).toBe(false);
});
