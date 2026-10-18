import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import SimilaritySearch from "../app/passport/similarity-search";
import { ApiError } from "../lib/api-client";
import type { PhotoUploadCommand } from "../lib/persona-photos";
import type { SearchCommand } from "../lib/persona-similarity-contracts";
import { detected } from "./face-fixtures";
import { preparedSource } from "./prepared-write-fixtures";
import {
  queryImage,
  queryReceipt,
  similarityPage,
} from "./similarity-fixtures";

beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:synthetic");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function source() {
  const value = preparedSource();
  value.similarity = {
    workspaceId: value.workspaceId,
    readiness: vi.fn(async () => ({
      workspace_id: value.workspaceId,
      state: "ready" as const,
      policy_id: "synthetic-reviewed-policy",
    })),
    prepare: vi.fn(async (command: PhotoUploadCommand) => ({
      ...queryReceipt(),
      query_id: command.request_id,
      source_sha256: command.sha256,
    })),
    search: vi.fn(async (command: SearchCommand) => similarityPage(command)),
    clear: vi.fn(async () => undefined),
    thumbnail: vi.fn(async () => new Blob(["fixture"])),
  };
  value.captures = {
    workspaceId: value.workspaceId,
    query: vi.fn(),
    thumbnail: vi.fn(async () => new Blob(["fixture"])),
  };
  value.faces = {
    workspaceId: value.workspaceId,
    query: vi.fn(async () => ({
      workspace_id: value.workspaceId,
      version_id: detected.version_id,
      portrait_id: detected.portrait_id,
      latest: {
        ...detected,
        generation_id: detected.generation_id,
        parent_id: detected.generation_id,
        selected: 0,
        state: "represented" as const,
        representation: similarityPage().representation,
      },
      provider_ready: false,
    })),
    process: vi.fn(),
  };
  return value;
}
async function prepare() {
  fireEvent.click(screen.getByText("Search by face similarity"));
  fireEvent.click(
    screen.getByRole("button", { name: "Check search readiness" }),
  );
  await screen.findByText(/search is ready under/);
  fireEvent.change(screen.getByLabelText("Choose face query image"), {
    target: { files: [queryImage()] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Prepare face query" }));
  await waitFor(() =>
    expect((screen.getAllByRole("radio")[0] as HTMLInputElement).disabled).toBe(
      false,
    ),
  );
}
function confirm() {
  fireEvent.click(screen.getAllByRole("radio")[1]);
  fireEvent.click(screen.getByRole("checkbox"));
}
it("does not call processing on file choice and requires confirmed face; exposes scope and fresh comparison", async () => {
  const value = source();
  render(<SimilaritySearch source={value} />);
  expect(value.similarity!.readiness).not.toHaveBeenCalled();
  await prepare();
  expect(value.similarity!.search).not.toHaveBeenCalled();
  const search = screen.getByRole("button", {
    name: "Search approved references",
  }) as HTMLButtonElement;
  expect(search.disabled).toBe(true);
  fireEvent.click(screen.getAllByRole("radio")[1]);
  expect(search.disabled).toBe(true);
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.change(screen.getByLabelText("Similarity scope"), {
    target: { value: "history" },
  });
  fireEvent.click(search);
  const compare = await screen.findByRole("button", { name: /Compare/ });
  expect(value.similarity!.search).toHaveBeenCalledWith(
    expect.objectContaining({ face_index: 1, scope: "history" }),
    expect.any(AbortSignal),
  );
  expect(screen.getByText(/face cosine 0.9500/)).toBeDefined();
  fireEvent.click(compare);
  await screen.findByText(/Matched approved reference/);
  expect(value.faces!.query).toHaveBeenCalledWith(
    expect.objectContaining({ portrait_id: detected.portrait_id }),
    expect.any(AbortSignal),
  );
  expect(value.faces!.process).not.toHaveBeenCalled();
});
it("retries exact prepare intent and reports unconfirmed clearing", async () => {
  const value = source(),
    prepareCall = value.similarity!.prepare as ReturnType<typeof vi.fn>;
  prepareCall.mockRejectedValueOnce(new ApiError("Unavailable", 503));
  value.similarity!.clear = vi
    .fn()
    .mockRejectedValueOnce(new ApiError("Unavailable", 503))
    .mockResolvedValue(undefined);
  render(<SimilaritySearch source={value} />);
  fireEvent.click(screen.getByText("Search by face similarity"));
  fireEvent.click(
    screen.getByRole("button", { name: "Check search readiness" }),
  );
  await screen.findByText(/search is ready under/);
  fireEvent.change(screen.getByLabelText("Choose face query image"), {
    target: { files: [queryImage()] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Prepare face query" }));
  fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
  await screen.findByLabelText("Select query face");
  expect(prepareCall.mock.calls[1][0]).toEqual(prepareCall.mock.calls[0][0]);
  fireEvent.click(screen.getByRole("button", { name: "Clear face query" }));
  await screen.findByText(/Server clearing is unconfirmed/);
  expect(screen.queryByLabelText("Select query face")).toBeNull();
  fireEvent.click(
    screen.getByRole("button", { name: "Retry server clearing" }),
  );
  await screen.findByText("Server query cleared.");
});
it.each([403, 410])(
  "clears query/result/preview on access loss or expiry %s",
  async (status) => {
    const value = source();
    value.similarity!.search = vi
      .fn()
      .mockRejectedValue(new ApiError("Unavailable", status));
    render(<SimilaritySearch source={value} />);
    await prepare();
    confirm();
    fireEvent.click(
      screen.getByRole("button", { name: "Search approved references" }),
    );
    await screen.findByText(
      status === 403
        ? /Workspace access was lost/
        : /Query expired or was cleared/,
    );
    expect(screen.queryByLabelText("Select query face")).toBeNull();
    expect(screen.queryByLabelText("Face similarity results")).toBeNull();
    expect(URL.revokeObjectURL).toHaveBeenCalled();
    await waitFor(() => expect(value.similarity!.clear).toHaveBeenCalled());
  },
);
it("ignores late preparation after clear and asks server to close its known query ID", async () => {
  const value = source();
  let finish: (r: ReturnType<typeof queryReceipt>) => void = () => {};
  value.similarity!.prepare = vi.fn(
    () =>
      new Promise<ReturnType<typeof queryReceipt>>((resolve) => {
        finish = resolve;
      }),
  );
  render(<SimilaritySearch source={value} />);
  fireEvent.click(screen.getByText("Search by face similarity"));
  fireEvent.click(
    screen.getByRole("button", { name: "Check search readiness" }),
  );
  await screen.findByText(/search is ready under/);
  fireEvent.change(screen.getByLabelText("Choose face query image"), {
    target: { files: [queryImage()] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Prepare face query" }));
  await waitFor(() => expect(value.similarity!.prepare).toHaveBeenCalled());
  fireEvent.click(screen.getByRole("button", { name: "Clear face query" }));
  await act(async () => finish(queryReceipt()));
  expect(screen.queryByLabelText("Select query face")).toBeNull();
  expect(value.similarity!.clear).toHaveBeenCalled();
});
it("shows the calibration gate and prevents uploading into an unready search", async () => {
  const value = source();
  value.similarity!.readiness = vi.fn(async () => ({
    workspace_id: value.workspaceId,
    state: "calibration_required" as const,
    policy_id: null,
  }));
  render(<SimilaritySearch source={value} />);
  fireEvent.click(screen.getByText("Search by face similarity"));
  fireEvent.click(
    screen.getByRole("button", { name: "Check search readiness" }),
  );
  await screen.findByText(/reviewed benchmark and calibration policy/);
  expect(
    (screen.getByLabelText("Choose face query image") as HTMLInputElement)
      .disabled,
  ).toBe(true);
  expect(value.similarity!.prepare).not.toHaveBeenCalled();
});

it("expires a prepared receipt automatically and cleans its preview", async () => {
  const value = source();
  value.similarity!.prepare = vi.fn(async (command) => {
    const now = Date.now();
    return {
      ...queryReceipt(),
      query_id: command.request_id,
      source_sha256: command.sha256,
      issued_at: new Date(now - 600001).toISOString(),
      expires_at: new Date(now - 1).toISOString(),
    };
  });
  render(<SimilaritySearch source={value} />);
  fireEvent.click(screen.getByText("Search by face similarity"));
  fireEvent.click(
    screen.getByRole("button", { name: "Check search readiness" }),
  );
  await screen.findByText(/search is ready under/);
  fireEvent.change(screen.getByLabelText("Choose face query image"), {
    target: { files: [queryImage()] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Prepare face query" }));
  await screen.findByText("Query expired. Prepare a new image query.");
  expect(screen.queryByLabelText("Select query face")).toBeNull();
  expect(value.similarity!.clear).toHaveBeenCalled();
});

it("shows no face detection without a selection or search action", async () => {
  const value = source();
  value.similarity!.prepare = vi.fn(async (command) => ({
    ...queryReceipt(),
    query_id: command.request_id,
    source_sha256: command.sha256,
    faces: [],
    state: "no_face" as const,
  }));
  render(<SimilaritySearch source={value} />);
  fireEvent.click(screen.getByText("Search by face similarity"));
  fireEvent.click(
    screen.getByRole("button", { name: "Check search readiness" }),
  );
  await screen.findByText(/search is ready under/);
  fireEvent.change(screen.getByLabelText("Choose face query image"), {
    target: { files: [queryImage()] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Prepare face query" }));
  await screen.findByText("No face detected. Prepare another image.");
  expect(screen.queryByRole("radio")).toBeNull();
  expect(value.similarity!.search).not.toHaveBeenCalled();
});

it("clears server query on unmount and rejects a newly changed current head during comparison", async () => {
  const value = source();
  value.gateway.load = vi.fn(async () => ({
    ...similarityPage().items[0].version,
    version_id: crypto.randomUUID(),
  }));
  const mounted = render(<SimilaritySearch source={value} />);
  await prepare();
  confirm();
  fireEvent.click(
    screen.getByRole("button", { name: "Search approved references" }),
  );
  fireEvent.click(await screen.findByRole("button", { name: /Compare/ }));
  await screen.findByText(/response could not be validated/);
  expect(value.gateway.load).toHaveBeenCalledWith(
    similarityPage().items[0].version.persona_id,
    null,
    expect.any(AbortSignal),
  );
  expect(value.captures!.thumbnail).not.toHaveBeenCalled();
  mounted.unmount();
  expect(value.similarity!.clear).toHaveBeenCalled();
});
