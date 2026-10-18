import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import PassportStudio from "../app/passport/studio";
import { preparedSource, receipt } from "./prepared-write-fixtures";
import { ApiError } from "../lib/api-client";
import type {
  PhotoUploadCommand,
  PhotoUploadReceipt,
} from "../lib/persona-photos";
import type { SaveCommand } from "../lib/persona-contracts";
import type { PersonaTransport } from "../lib/persona-gateway";

beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:synthetic");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function image() {
  const file = new File(["synthetic"], "portrait.png", { type: "image/png" });
  Object.defineProperty(file, "arrayBuffer", {
    value: async () => new TextEncoder().encode("synthetic").buffer,
  });
  return file;
}
function photoReceipt(
  command: PhotoUploadCommand,
  workspace: string,
): PhotoUploadReceipt {
  return {
    id: "00000000-0000-4000-8000-000000000090",
    workspace_id: workspace,
    request_id: command.request_id,
    sha256: command.sha256,
    width: 32,
    height: 16,
  };
}
function create() {
  fireEvent.click(screen.getByRole("button", { name: "New capture" }));
  for (const label of [
    "Persona name",
    "Biography",
    "Human contribution",
    "AI disclosure",
  ])
    fireEvent.change(screen.getByLabelText(label), {
      target: { value: "Authored text" },
    });
}
function pick() {
  fireEvent.change(screen.getByLabelText("Choose photo"), {
    target: { files: [image()] },
  });
}
function confirm() {
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I confirm these details/ }),
  );
}
function disabled() {
  return (
    screen.getByRole("button", {
      name: "Register persona",
    }) as HTMLButtonElement
  ).disabled;
}

it("previews locally without a photo connection and never saves an unchecked selection", () => {
  const source = preparedSource();
  render(<PassportStudio savedSource={source} />);
  create();
  expect(
    screen.getByRole("heading", { name: /Persona portrait/ }),
  ).toBeDefined();
  const picker = screen.getByLabelText("Choose photo") as HTMLInputElement;
  expect(picker.disabled).toBe(false);
  confirm();
  expect(disabled()).toBe(true);
  pick();
  expect(screen.getByAltText("Unsaved photo selection")).toBeDefined();
  expect(screen.getByText(/portrait.png ·/)).toBeDefined();
  fireEvent.click(screen.getByRole("button", { name: /Capture helper/ }));
  expect(
    screen.getAllByRole("button", { name: /Scan portrait/ }).length,
  ).toBeGreaterThan(0);
  expect(screen.queryByText("A face for your persona")).toBeNull();
  confirm();
  expect(disabled()).toBe(true);
  expect(
    (
      screen.getByRole("button", {
        name: "Scan",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Discard selection" }));
  expect(screen.getByText("A face for your persona")).toBeDefined();
  confirm();
  expect(disabled()).toBe(true);
});

it("rejects invalid local files and releases the previous preview without losing text", () => {
  render(<PassportStudio savedSource={preparedSource()} />);
  create();
  pick();
  fireEvent.change(screen.getByLabelText("Choose photo"), {
    target: {
      files: [new File(["invalid"], "portrait.svg", { type: "image/svg+xml" })],
    },
  });
  expect(screen.getByRole("alert").textContent).toMatch(/PNG or JPEG/);
  expect(screen.queryByAltText("Unsaved photo selection")).toBeNull();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:synthetic");
  expect(
    (screen.getByLabelText("Biography") as HTMLTextAreaElement).value,
  ).toBe("Authored text");
});

it("ingests only after Scan, keeps its exact retry and saves the attachment with text", async () => {
  const write = vi.fn<PersonaTransport>(async (op, _workspace, command) =>
    receipt(op, command),
  );
  const source = preparedSource(write);
  const upload = vi.fn(async (command: PhotoUploadCommand) => {
    if (upload.mock.calls.length === 1) throw new ApiError("Unavailable", 503);
    return photoReceipt(command, source.workspaceId);
  });
  source.photos = {
    workspaceId: source.workspaceId,
    upload,
    thumbnail: async () => null,
  };
  render(<PassportStudio savedSource={source} />);
  create();
  confirm();
  expect(disabled()).toBe(true);
  pick();
  expect(disabled()).toBe(true);
  expect(screen.getByAltText("Unsaved photo selection")).toBeDefined();
  confirm();
  expect(disabled()).toBe(true);
  await act(async () => {});
  expect(upload).not.toHaveBeenCalled();
  expect(write).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Scan" }));
  await screen.findByRole("button", { name: "Retry scan" });
  expect(
    (screen.getByLabelText("Biography") as HTMLTextAreaElement).value,
  ).toBe("Authored text");
  fireEvent.click(screen.getByRole("button", { name: "Retry scan" }));
  await screen.findByText(/Scan complete\. Save/);
  expect(upload.mock.calls[0][0]).toEqual(upload.mock.calls[1][0]);
  expect(disabled()).toBe(false);
  fireEvent.click(screen.getByRole("button", { name: "Register persona" }));
  await screen.findByRole("heading", { name: "System Capture saved" });
  expect((write.mock.calls[0][2] as SaveCommand).photo).toEqual({
    action: "attach",
    upload_id: "00000000-0000-4000-8000-000000000090",
  });
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:synthetic");
});

it("ignores a cancelled late upload receipt and preserves text when discarding the photo", async () => {
  const source = preparedSource();
  let finish: (value: PhotoUploadReceipt) => void = () => {};
  const upload = vi.fn(
    (...args: [PhotoUploadCommand, AbortSignal]) =>
      new Promise<PhotoUploadReceipt>((resolve) => {
        expect(args[1]).toBeInstanceOf(AbortSignal);
        finish = resolve;
      }),
  );
  source.photos = {
    workspaceId: source.workspaceId,
    upload,
    thumbnail: async () => null,
  };
  render(<PassportStudio savedSource={source} />);
  create();
  pick();
  confirm();
  fireEvent.click(screen.getByRole("button", { name: "Scan" }));
  await waitFor(() => expect(upload).toHaveBeenCalledTimes(1));
  expect(
    (screen.getByRole("button", { name: "Scanning…" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  expect(disabled()).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Stop waiting" }));
  await act(async () =>
    finish(photoReceipt(upload.mock.calls[0][0], source.workspaceId)),
  );
  expect(screen.queryByText(/Scan complete/)).toBeNull();
  expect(disabled()).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Discard selection" }));
  expect(screen.queryByAltText("Unsaved photo selection")).toBeNull();
  expect(
    (screen.getByLabelText("Persona name") as HTMLInputElement).value,
  ).toBe("Authored text");
  confirm();
  expect(disabled()).toBe(true);
});

it("requires a portrait even with valid text, confirmation and a connected photo service", async () => {
  const write = vi.fn<PersonaTransport>();
  const source = preparedSource(write);
  const upload = vi.fn();
  source.photos = {
    workspaceId: source.workspaceId,
    upload,
    thumbnail: async () => null,
  };
  render(<PassportStudio savedSource={source} />);
  create();
  confirm();
  expect(
    screen.getByRole("heading", { name: /Persona portrait required/ }),
  ).toBeDefined();
  fireEvent.click(screen.getByRole("button", { name: /Capture helper/ }));
  expect(
    screen.getAllByRole("button", { name: /Choose portrait/ }).length,
  ).toBeGreaterThan(0);
  expect(disabled()).toBe(true);
  fireEvent.submit(screen.getByRole("form", { name: "System Capture" }));
  await act(async () => {});
  expect(write).not.toHaveBeenCalled();
  expect(upload).not.toHaveBeenCalled();
});

it("rejects another workspace's upload receipt and clears selection on session change", async () => {
  const source = preparedSource();
  source.photos = {
    workspaceId: source.workspaceId,
    upload: async (command) => photoReceipt(command, crypto.randomUUID()),
    thumbnail: async () => null,
  };
  const mounted = render(<PassportStudio savedSource={source} />);
  create();
  pick();
  confirm();
  fireEvent.click(screen.getByRole("button", { name: "Scan" }));
  await screen.findByText(/Photo scan could not be confirmed/);
  expect(disabled()).toBe(true);
  mounted.rerender(
    <PassportStudio savedSource={{ ...source, sessionKey: "other-session" }} />,
  );
  expect(screen.queryByAltText("Unsaved photo selection")).toBeNull();
  expect(
    (screen.getByLabelText("Persona name") as HTMLInputElement).value,
  ).toBe("");
});

it("saves photo removal as an explicit new-version intent", async () => {
  const write = vi.fn<PersonaTransport>(async (op, _workspace, command) =>
    receipt(op, command),
  );
  const source = preparedSource(write);
  source.photos = {
    workspaceId: source.workspaceId,
    upload: vi.fn(),
    thumbnail: async () => null,
  };
  render(<PassportStudio savedSource={source} />);
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  fireEvent.click(await screen.findByRole("button", { name: "Edit persona" }));
  fireEvent.click(screen.getByRole("button", { name: "Remove saved photo" }));
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I have reviewed this draft/ }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Save version" }));
  await screen.findByText(/Storage receipt validated/);
  expect((write.mock.calls[0][2] as SaveCommand).photo).toEqual({
    action: "remove",
    upload_id: null,
  });
  expect((write.mock.calls[0][2] as SaveCommand).expected_revision).toBe(1);
});

it("blocks further saving after photo authorization loss while retaining authored text", async () => {
  const source = preparedSource();
  source.photos = {
    workspaceId: source.workspaceId,
    upload: async () => {
      throw new ApiError("Denied", 403);
    },
    thumbnail: async () => null,
  };
  render(<PassportStudio savedSource={source} />);
  create();
  pick();
  confirm();
  fireEvent.click(screen.getByRole("button", { name: "Scan" }));
  await screen.findByText(/Photo access denied/);
  fireEvent.click(screen.getByRole("button", { name: "Discard selection" }));
  confirm();
  expect(disabled()).toBe(true);
  expect(
    (screen.getByLabelText("Persona name") as HTMLInputElement).value,
  ).toBe("Authored text");
});
