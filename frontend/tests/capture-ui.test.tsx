import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import SavedCaptures from "../app/passport/saved-captures";
import ReferenceEditor from "../app/passport/reference-editor";
import { ApiError } from "../lib/api-client";
import type { PersonaTransport } from "../lib/persona-gateway";
import type { SaveCommand } from "../lib/persona-contracts";
import { profile, capture } from "./capture-fixtures";
import {
  draftProvider,
  preparedSource,
  receipt,
  version,
} from "./prepared-write-fixtures";
import { portraitGateway } from "./portrait-fixtures";

beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:synthetic");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function source(write?: PersonaTransport) {
  const value = preparedSource(write);
  value.photos = portraitGateway(value.workspaceId);
  value.captures = {
    workspaceId: value.workspaceId,
    query: vi.fn(async () => profile),
    thumbnail: vi.fn(
      async () => new Blob(["synthetic"], { type: "image/png" }),
    ),
  };
  return value;
}
function confirm() {
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: /I approve this ordered reference set/,
    }),
  );
}
function save() {
  fireEvent.click(
    screen.getByRole("button", { name: "Save reference version" }),
  );
}

it("queries only on inspection and releases authorized thumbnails on close", async () => {
  const value = source(),
    denied = vi.fn();
  render(<SavedCaptures source={value} version={version} denied={denied} />);
  expect(value.captures!.query).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect capture and references" }),
  );
  await screen.findByRole("heading", { name: /Approved references/ });
  await waitFor(() =>
    expect(screen.getAllByAltText("Approved reference portrait")).toHaveLength(
      2,
    ),
  );
  expect(screen.getAllByText("Analysis image prepared")).toHaveLength(3);
  expect(value.captures!.thumbnail).toHaveBeenCalledWith(
    version.version_id,
    capture.portrait_id,
    expect.any(AbortSignal),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Close capture and references" }),
  );
  expect(URL.revokeObjectURL).toHaveBeenCalledTimes(2);
  expect(denied).not.toHaveBeenCalled();
});
it("orders and clears references explicitly, preserving content and exact retry", async () => {
  const write = vi.fn<PersonaTransport>(async (op, _ws, command) => {
    if (write.mock.calls.length === 1) throw new ApiError("Unavailable", 503);
    return receipt(op, command);
  });
  const value = source(write);
  render(
    draftProvider(
      new Map(),
      <ReferenceEditor
        source={value}
        version={version}
        denied={vi.fn()}
        references={profile.references}
      />,
    ),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Move reference 2 earlier" }),
  );
  confirm();
  save();
  await screen.findByRole("button", { name: "Retry same intent" });
  expect(
    (
      screen.getByRole("button", {
        name: "Save reference version",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Retry same intent" }));
  await screen.findByText(/Storage receipt validated/);
  const command = write.mock.calls[0][2] as SaveCommand;
  expect(write.mock.calls[1][2]).toEqual(command);
  expect(command.references?.upload_ids).toEqual(
    [...profile.references].reverse().map((item) => item.portrait_id),
  );
  expect(command.content).toEqual(version.content);
  expect(command.expected_revision).toBe(version.revision);
  expect(command.photo).toEqual({ action: "keep", upload_id: null });
});
it("saves an explicitly empty set and does not fetch or store portraits just by opening editor", async () => {
  const write = vi.fn<PersonaTransport>(async (op, _ws, command) =>
    receipt(op, command),
  );
  const value = source(write),
    store = new Map();
  render(
    draftProvider(
      store,
      <ReferenceEditor
        source={value}
        version={version}
        denied={vi.fn()}
        references={profile.references}
      />,
    ),
  );
  expect(store.size).toBe(0);
  expect(value.captures!.query).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Clear all references" }));
  confirm();
  save();
  await screen.findByText(/Storage receipt validated/);
  expect((write.mock.calls[0][2] as SaveCommand).references).toEqual({
    action: "replace",
    upload_ids: [],
  });
});
it("clears capture results on known access loss and ignores cancelled late reads", async () => {
  const value = source(),
    denied = vi.fn();
  value.captures!.query = vi.fn(async () => {
    throw new ApiError("Denied", 403);
  });
  render(<SavedCaptures source={value} version={version} denied={denied} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect capture and references" }),
  );
  await waitFor(() => expect(denied).toHaveBeenCalledTimes(1));
  expect(screen.queryByText("Analysis image prepared")).toBeNull();
  await act(async () => {});
});

it("scans a new reference but requires explicit addition and confirmation to approve it", async () => {
  const write = vi.fn<PersonaTransport>(async (op, _ws, command) =>
    receipt(op, command),
  );
  const value = stagedReferenceSource(write);
  render(
    draftProvider(
      new Map(),
      <ReferenceEditor
        source={value}
        version={version}
        denied={vi.fn()}
        references={[]}
      />,
    ),
  );
  const file = new File(["synthetic"], "ref.png", { type: "image/png" });
  Object.defineProperty(file, "arrayBuffer", {
    value: async () => new TextEncoder().encode("synthetic").buffer,
  });
  fireEvent.change(screen.getByLabelText("Add or replace photo"), {
    target: { files: [file] },
  });
  expect(value.photos!.upload).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Scan" }));
  await screen.findByText(/Scan complete\. Save/);
  const add = await screen.findByRole("button", {
    name: "Add checked reference",
  });
  await waitFor(() => expect((add as HTMLButtonElement).disabled).toBe(false));
  expect(screen.getByText("0 of 8 selected")).toBeDefined();
  expect(write).not.toHaveBeenCalled();
  fireEvent.click(add);
  expect(screen.getByText("1 of 8 selected")).toBeDefined();
  expect(screen.getByAltText("Unsaved reference 1 preview")).toBeDefined();
  expect(
    (
      screen.getByRole("button", {
        name: "Save reference version",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  confirm();
  save();
  await screen.findByText(/Storage receipt validated/);
  expect(
    (write.mock.calls[0][2] as SaveCommand).references?.upload_ids,
  ).toEqual([capture.portrait_id]);
});

it("bounds the editor at eight and blocks stale conflicts until a fresh record is opened", async () => {
  const write = vi.fn<PersonaTransport>(async () => {
    throw new ApiError("Conflict", 409);
  });
  const value = source(write);
  const refs = Array.from({ length: 8 }, () => ({
    ...capture,
    portrait_id: crypto.randomUUID(),
  }));
  render(
    draftProvider(
      new Map(),
      <ReferenceEditor
        source={value}
        version={version}
        denied={vi.fn()}
        references={refs}
      />,
    ),
  );
  expect(screen.queryByLabelText("Add or replace photo")).toBeNull();
  confirm();
  save();
  await screen.findByText(/Reopen the latest saved record/);
  expect(
    (
      screen.getByRole("button", {
        name: "Save reference version",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  expect(write).toHaveBeenCalledTimes(1);
});

it("ignores a late profile after the inspection is closed", async () => {
  const value = source();
  let finish: (result: typeof profile) => void = () => {};
  value.captures!.query = vi.fn(
    () =>
      new Promise<typeof profile>((resolve) => {
        finish = resolve;
      }),
  );
  render(<SavedCaptures source={value} version={version} denied={vi.fn()} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect capture and references" }),
  );
  await waitFor(() => expect(value.captures!.query).toHaveBeenCalledTimes(1));
  fireEvent.click(
    screen.getByRole("button", { name: "Close capture and references" }),
  );
  await act(async () => finish(profile));
  expect(screen.queryByText("Analysis image prepared")).toBeNull();
  expect(value.captures!.thumbnail).not.toHaveBeenCalled();
});

it("preserves an uncertain ordered intent across a newer record instead of creating another save", async () => {
  const write = vi.fn<PersonaTransport>(async (op, _ws, command) => {
    if (write.mock.calls.length === 1) throw new ApiError("Unavailable", 503);
    return receipt(op, command);
  });
  const value = source(write),
    store = new Map();
  const renderEditor = (revision: number) =>
    draftProvider(
      store,
      <ReferenceEditor
        key={revision}
        source={value}
        version={{ ...version, revision }}
        denied={vi.fn()}
        references={profile.references}
      />,
    );
  const mounted = render(renderEditor(1));
  fireEvent.click(
    screen.getByRole("button", { name: "Move reference 2 earlier" }),
  );
  confirm();
  save();
  await screen.findByRole("button", { name: "Retry same intent" });
  mounted.rerender(renderEditor(2));
  expect(
    (
      screen.getByRole("button", {
        name: "Save reference version",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Retry same intent" }));
  await screen.findByText(/Storage receipt validated/);
  expect(write.mock.calls[1][2]).toEqual(write.mock.calls[0][2]);
});

it("requires fresh record inspection and new confirmation after a reference conflict", async () => {
  const write = vi.fn<PersonaTransport>(async (op, _ws, command) => {
    if (write.mock.calls.length === 1) throw new ApiError("Conflict", 409);
    return receipt(op, command);
  });
  const value = source(write),
    store = new Map();
  const editor = (revision: number) =>
    draftProvider(
      store,
      <ReferenceEditor
        key={revision}
        source={value}
        version={{ ...version, revision }}
        denied={vi.fn()}
        references={profile.references}
      />,
    );
  const mounted = render(editor(1));
  confirm();
  save();
  await screen.findByText(/Reopen the latest saved record/);
  expect(
    screen.queryByRole("button", { name: "Prepare references for version 1" }),
  ).toBeNull();
  mounted.rerender(editor(2));
  fireEvent.click(
    screen.getByRole("button", { name: "Prepare references for version 2" }),
  );
  expect(
    (
      screen.getByRole("button", {
        name: "Save reference version",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  confirm();
  save();
  await screen.findByText(/Storage receipt validated/);
  expect((write.mock.calls[1][2] as SaveCommand).expected_revision).toBe(2);
});

function stagedReferenceSource(write: PersonaTransport) {
  const value = source(write);
  let digest = "";
  value.photos!.upload = vi.fn(async (command) => {
    digest = command.sha256;
    return {
      id: capture.portrait_id,
      workspace_id: value.workspaceId,
      request_id: command.request_id,
      sha256: digest,
      width: 32,
      height: 16,
    };
  });
  value.captures!.query = vi.fn(async (command) => ({
    ...profile,
    ...command,
    capture: { ...capture, source_sha256: digest },
    references: [],
  }));
  return value;
}
