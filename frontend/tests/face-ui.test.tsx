import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import FaceInspection from "../app/passport/face-inspection";
import { ApiError } from "../lib/api-client";
import type { FaceCommand, FaceResult } from "../lib/persona-faces";
import { capture } from "./capture-fixtures";
import { detected } from "./face-fixtures";
import {
  draftProvider,
  preparedSource,
  version,
} from "./prepared-write-fixtures";

beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:synthetic");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function source(ready = true) {
  const value = preparedSource();
  value.captures = {
    workspaceId: value.workspaceId,
    query: vi.fn(),
    thumbnail: vi.fn(async () => new Blob(["fixture"])),
  };
  value.faces = {
    workspaceId: value.workspaceId,
    query: vi.fn(async () => ({
      workspace_id: value.workspaceId,
      version_id: version.version_id,
      portrait_id: capture.portrait_id,
      latest: detected,
      provider_ready: ready,
    })),
    process: vi.fn(async (command: FaceCommand): Promise<FaceResult> => ({
      ...detected,
      request_id: command.request_id,
      generation_id: crypto.randomUUID(),
      parent_id: command.generation_id,
      selected: command.face_index,
      state: "quality_blocked",
      reasons: ["small_face"],
    })),
  };
  return value;
}
function open() {
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect face processing" }),
  );
}
it("requires face choice and explicit confirmation before representation and shows quality", async () => {
  const value = source();
  render(
    draftProvider(
      new Map(),
      <FaceInspection
        source={value}
        version={version}
        capture={capture}
        denied={vi.fn()}
      />,
    ),
  );
  expect(value.faces!.query).not.toHaveBeenCalled();
  open();
  const create = await screen.findByRole("button", {
    name: "Create face and image representations",
  });
  expect((create as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getAllByRole("radio")[1]);
  expect((create as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(create);
  await screen.findByText(/Quality blocked: small face/);
  expect(value.faces!.process).toHaveBeenCalledWith(
    expect.objectContaining({
      face_index: 1,
      generation_id: detected.generation_id,
      version_id: version.version_id,
    }),
    expect.any(AbortSignal),
  );
});
it("disables live actions when provider is unavailable but shows stored provenance", async () => {
  const value = source(false);
  render(
    <FaceInspection
      source={value}
      version={version}
      capture={capture}
      denied={vi.fn()}
    />,
  );
  open();
  const run = await screen.findByRole("button", { name: "Run face detection" });
  expect((run as HTMLButtonElement).disabled).toBe(true);
  expect(screen.getByText("Face processing provenance")).toBeDefined();
  expect(value.faces!.process).not.toHaveBeenCalled();
});
it("retains an uncertain request across close and reopen and retries identical intent", async () => {
  const value = source(),
    store = new Map();
  value.faces!.process = vi.fn(async (command) => {
    if (
      (value.faces!.process as ReturnType<typeof vi.fn>).mock.calls.length === 1
    )
      throw new ApiError("Unavailable", 503);
    return { ...detected, request_id: command.request_id };
  });
  render(
    draftProvider(
      store,
      <FaceInspection
        source={value}
        version={version}
        capture={capture}
        denied={vi.fn()}
      />,
    ),
  );
  open();
  fireEvent.click(
    await screen.findByRole("button", { name: "Run face detection" }),
  );
  await screen.findByRole("button", { name: "Retry same face request" });
  fireEvent.click(
    screen.getByRole("button", { name: "Close face processing" }),
  );
  open();
  fireEvent.click(
    await screen.findByRole("button", { name: "Retry same face request" }),
  );
  await waitFor(() => expect(value.faces!.process).toHaveBeenCalledTimes(2));
  const calls = (value.faces!.process as ReturnType<typeof vi.fn>).mock.calls;
  expect(calls[1][0]).toEqual(calls[0][0]);
  await act(async () => {});
});
