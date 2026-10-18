import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PassportStudio from "../app/passport/studio";
import { ApiError } from "../lib/api-client";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import type { PhotoUploadCommand } from "../lib/persona-photos";
import type { PortraitSearchPage } from "../lib/persona-portrait-search";
import { preparedSource } from "./prepared-write-fixtures";
import wire from "./fixtures/persona-wire.json";

afterEach(cleanup);
function image() {
  const file = new File(["synthetic"], "query.png", { type: "image/png" });
  Object.defineProperty(file, "arrayBuffer", {
    value: async () => new TextEncoder().encode("synthetic").buffer,
  });
  return file;
}
function response(command: PhotoUploadCommand): PortraitSearchPage {
  return {
    workspace_id: wire.version.workspace_id,
    request_id: command.request_id,
    sha256: command.sha256,
    method: "exact_file_sha256",
    items: [wire.version],
    has_more: false,
  };
}
function connected() {
  const source = preparedSource();
  const read = vi.fn<PersonaTransport>(async (operation) =>
    operation === "gallery" ? wire.gallery : wire.version,
  );
  source.gateway = personaGateway(source.workspaceId, read);
  const search = vi.fn(
    async (command: PhotoUploadCommand, signal: AbortSignal) => {
      expect(signal).toBeInstanceOf(AbortSignal);
      return response(command);
    },
  );
  source.portraitSearch = { workspaceId: source.workspaceId, search };
  return { source, search, read };
}
function pick() {
  fireEvent.click(screen.getByRole("button", { name: "Search by image" }));
  fireEvent.change(screen.getByLabelText("Choose search image"), {
    target: { files: [image()] },
  });
}

it("does not search or enroll on selection; returns labelled exact-file evidence and freshly reads matching version", async () => {
  const { source, search, read } = connected();
  const upload = vi.fn();
  source.photos = {
    workspaceId: source.workspaceId,
    upload,
    thumbnail: async () => null,
  };
  render(<PassportStudio savedSource={source} />);
  await screen.findByRole("button", { name: /Open record/ });
  pick();
  await act(async () => {});
  expect(search).not.toHaveBeenCalled();
  expect(upload).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Find identical portraits" }),
  );
  const inspect = await screen.findByRole("button", {
    name: /matching version 1/,
  });
  expect(
    screen.getByText(/1 persona with identical portrait bytes/),
  ).toBeDefined();
  expect(screen.getByText(/Use the face similarity panel/)).toBeDefined();
  fireEvent.click(inspect);
  await screen.findByLabelText("Matching portrait version");
  await screen.findByText("Version reference");
  expect(read).toHaveBeenCalledWith(
    "load",
    source.workspaceId,
    { persona_id: wire.version.persona_id, revision: 1 },
    expect.any(AbortSignal),
  );
  expect(upload).not.toHaveBeenCalled();
});

it("clears candidates when a fresh version read loses permission", async () => {
  const { source, read } = connected();
  read.mockImplementation(async (operation) => {
    if (operation === "gallery") return wire.gallery;
    throw new ApiError("Denied", 403);
  });
  render(<PassportStudio savedSource={source} />);
  pick();
  fireEvent.click(
    screen.getByRole("button", { name: "Find identical portraits" }),
  );
  fireEvent.click(
    await screen.findByRole("button", { name: /matching version 1/ }),
  );
  await screen.findByText(/Workspace access is no longer available/);
  expect(screen.queryByLabelText("Portrait search results")).toBeNull();
  expect(screen.queryByLabelText("Matching portrait version")).toBeNull();
});

it("ignores cancelled late candidates and clears image state on session change", async () => {
  const { source, search } = connected();
  let finish: (page: PortraitSearchPage) => void = () => {};
  search.mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const mounted = render(<PassportStudio savedSource={source} />);
  await screen.findByRole("button", { name: /Open record/ });
  pick();
  fireEvent.click(
    screen.getByRole("button", { name: "Find identical portraits" }),
  );
  await waitFor(() => expect(search).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByRole("button", { name: "Stop loading" }));
  await act(async () => finish(response(search.mock.calls[0][0])));
  expect(screen.queryByLabelText("Portrait search results")).toBeNull();
  mounted.rerender(
    <PassportStudio savedSource={{ ...source, sessionKey: "new-session" }} />,
  );
  expect(screen.queryByText(/query.png/)).toBeNull();
});

it("distinguishes empty authorized results from an unavailable search", async () => {
  const { source, search } = connected();
  search.mockImplementation(async (command) => ({
    ...response(command),
    items: [],
  }));
  render(<PassportStudio savedSource={source} />);
  pick();
  fireEvent.click(
    screen.getByRole("button", { name: "Find identical portraits" }),
  );
  await screen.findByText(
    "No identical registered portrait found in this workspace.",
  );
  search.mockRejectedValue(new ApiError("Unavailable", 503));
  fireEvent.click(
    screen.getByRole("button", { name: "Find identical portraits" }),
  );
  await screen.findByText(/Saved records are temporarily unavailable/);
  expect(
    screen.queryByText(
      "No identical registered portrait found in this workspace.",
    ),
  ).toBeNull();
});

it.each([
  { type: "image/svg+xml", size: 9 },
  { type: "image/png", size: 0 },
  { type: "image/png", size: 10485761 },
])(
  "rejects invalid local queries before contacting the service %j",
  async ({ type, size }) => {
    const { source, search } = connected();
    render(<PassportStudio savedSource={source} />);
    pick();
    const invalid = new File(["synthetic"], "invalid-query", { type });
    Object.defineProperty(invalid, "size", { value: size });
    fireEvent.change(screen.getByLabelText("Choose search image"), {
      target: { files: [invalid] },
    });
    expect(screen.getByRole("alert").textContent).toMatch(
      /Choose a PNG or JPEG/,
    );
    expect(
      (
        screen.getByRole("button", {
          name: "Find identical portraits",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    await act(async () => {});
    expect(search).not.toHaveBeenCalled();
  },
);
