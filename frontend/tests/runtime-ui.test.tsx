import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import DurableFaceJobs from "../app/passport/durable-face-jobs";
import { ApiError } from "../lib/api-client";
import { capture } from "./capture-fixtures";
import { detected } from "./face-fixtures";
import { job, page, ready } from "./job-fixtures";
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
function fixture(items = [] as ReturnType<typeof job>[]) {
  const source = preparedSource();
  source.captures = {
    workspaceId: source.workspaceId,
    query: vi.fn(),
    thumbnail: vi.fn(async () => new Blob(["fixture"])),
  };
  source.runtime = {
    workspaceId: source.workspaceId,
    readiness: vi.fn(async () => ready),
    history: vi.fn(async () => ({ ...page, items })),
    enqueue: vi.fn(async (command) => job(command)),
    update: vi.fn(async () => ({
      ...job(),
      sequence: 1,
      state: "cancelled" as const,
    })),
  };
  const reloadResult = vi.fn(),
    denied = vi.fn();
  const element = (
    <DurableFaceJobs
      source={source}
      version={version}
      capture={capture}
      result={detected}
      reloadResult={reloadResult}
      denied={denied}
    />
  );
  return { source, element, reloadResult, denied };
}
it("requires explicit cloud cost confirmation and refresh after queued acknowledgement", async () => {
  const { source, element } = fixture();
  render(draftProvider(new Map(), element));
  const queue = await screen.findByRole("button", {
    name: "Queue face detection",
  });
  expect((queue as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getAllByRole("checkbox")[0]);
  fireEvent.click(queue);
  await screen.findByRole("button", { name: "Reload saved jobs" });
  expect((queue as HTMLButtonElement).disabled).toBe(true);
  expect(source.runtime!.enqueue).toHaveBeenCalledWith(
    expect.objectContaining({ generation_id: null, face_index: null }),
    expect.any(AbortSignal),
  );
});
it("requires performer selection and confirmation for queued representations", async () => {
  const { source, element } = fixture();
  render(draftProvider(new Map(), element));
  const queue = await screen.findByRole("button", {
    name: "Queue face and image representations",
  });
  fireEvent.click(screen.getAllByRole("checkbox")[0]);
  expect((queue as HTMLButtonElement).disabled).toBe(true);
  fireEvent.change(screen.getByRole("combobox"), { target: { value: "1" } });
  fireEvent.click(screen.getAllByRole("checkbox")[1]);
  fireEvent.click(queue);
  await waitFor(() =>
    expect(source.runtime!.enqueue).toHaveBeenCalledWith(
      expect.objectContaining({
        face_index: 1,
        generation_id: detected.generation_id,
      }),
      expect.any(AbortSignal),
    ),
  );
});
it("retains unknown outcome across remount and retries identical durable intent", async () => {
  const { source, element } = fixture(),
    drafts = new Map();
  source.runtime!.enqueue = vi
    .fn()
    .mockRejectedValueOnce(new ApiError("unavailable", 503))
    .mockImplementation(async (command) => job(command));
  const view = render(draftProvider(drafts, element));
  const queue = await screen.findByRole("button", {
    name: "Queue face detection",
  });
  fireEvent.click(screen.getAllByRole("checkbox")[0]);
  fireEvent.click(queue);
  await screen.findByRole("button", { name: "Retry same intent" });
  view.unmount();
  render(draftProvider(drafts, element));
  fireEvent.click(
    await screen.findByRole("button", { name: "Retry same intent" }),
  );
  await waitFor(() => expect(source.runtime!.enqueue).toHaveBeenCalledTimes(2));
  const calls = vi.mocked(source.runtime!.enqueue).mock.calls;
  expect(calls[0][0]).toEqual(calls[1][0]);
});
it("shows unavailable configuration without querying jobs or submitting providers", async () => {
  const { source, element } = fixture();
  source.runtime!.readiness = vi.fn(async () => ({
    ...ready,
    face_jobs_configured: false,
  }));
  render(element);
  await screen.findByText(/not configured on this connection/);
  expect(source.runtime!.history).not.toHaveBeenCalled();
  expect(source.runtime!.enqueue).not.toHaveBeenCalled();
});
it("recovers with exact job sequence and reloads completed results without processing", async () => {
  const failed = {
    ...job(),
    state: "failed" as const,
    attempts: 1,
    sequence: 2,
    recovery_available: true,
  };
  const { source, element, reloadResult } = fixture([
    failed,
    {
      ...job({ ...job().command, request_id: crypto.randomUUID() }),
      state: "succeeded",
      generation_id: detected.generation_id,
    },
  ]);
  render(draftProvider(new Map(), element));
  fireEvent.click(
    await screen.findByRole("button", {
      name: "Recover stalled or failed job",
    }),
  );
  await waitFor(() =>
    expect(source.runtime!.update).toHaveBeenCalledWith(
      expect.objectContaining({
        job_id: failed.job_id,
        expected_sequence: 2,
        action: "retry",
      }),
      expect.anything(),
      expect.any(AbortSignal),
    ),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Reload completed face result" }),
  );
  expect(reloadResult).toHaveBeenCalledOnce();
  expect(source.runtime!.enqueue).not.toHaveBeenCalled();
});
