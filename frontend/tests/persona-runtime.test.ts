import { afterEach, expect, it, vi } from "vitest";
import { apiClient } from "../lib/api-client";
import { parseJob, parseJobUpdate } from "../lib/persona-job-contracts";
import { parseReadiness, runtimeGateway } from "../lib/persona-runtime";
import { command, job, page, ready, subject } from "./job-fixtures";
import { version } from "./prepared-write-fixtures";

afterEach(() => vi.restoreAllMocks());
it.each([
  { job_id: crypto.randomUUID() },
  { attempts: 4 },
  { sequence: 33 },
  { state: "succeeded" },
  { state: "running" },
  { actor_ref: "browser" },
  { updated_at: "2020-01-01T00:00:00Z" },
  { lease_until: version.recorded_at },
  { command: { ...command, face_index: 0 } },
])("rejects incoherent or unsupported job receipts %j", (changes) => {
  expect(() => parseJob({ ...job(), ...changes })).toThrow();
});
it("does not present configured capabilities as live acceptance", () => {
  expect(parseReadiness(ready).acceptance).toBe("live_rehearsal_required");
  for (const changes of [
    { acceptance: "passed" },
    { investigation_configured: true },
    { signing_configured: true },
  ])
    expect(() => parseReadiness({ ...ready, ...changes })).toThrow();
  expect(() =>
    parseJobUpdate({
      job_id: job().job_id,
      request_id: crypto.randomUUID(),
      expected_sequence: true,
      action: "retry",
    }),
  ).toThrow();
});
it("exposes all human runtime routes privately without automatic retries", async () => {
  const update = {
    job_id: job().job_id,
    request_id: crypto.randomUUID(),
    expected_sequence: 0,
    action: "cancel" as const,
  };
  const post = vi
    .spyOn(apiClient, "post")
    .mockResolvedValueOnce(ready)
    .mockResolvedValueOnce(job())
    .mockResolvedValueOnce(page)
    .mockResolvedValueOnce({ ...job(), sequence: 1, state: "cancelled" });
  const gateway = runtimeGateway(version.workspace_id),
    signal = new AbortController().signal;
  await gateway.readiness(signal);
  await gateway.enqueue(command, signal);
  await gateway.history(subject, signal);
  await gateway.update(update, subject, signal);
  expect(post.mock.calls.map((call) => call[0].split("/").at(-1))).toEqual([
    "readiness",
    "enqueue",
    "history",
    "update",
  ]);
  expect(
    post.mock.calls.every(
      (call) =>
        call[2]?.retries === 0 &&
        call[2]?.cache === "no-store" &&
        call[2]?.redirect === "error",
    ),
  ).toBe(true);
});
it.each(["foreign", "changed", "duplicate", "stale", "late"])(
  "rejects %s results before display",
  async (mode) => {
    const post = vi.spyOn(apiClient, "post"),
      gateway = runtimeGateway(version.workspace_id),
      controller = new AbortController();
    if (mode === "foreign") {
      post.mockResolvedValue({ ...ready, workspace_id: crypto.randomUUID() });
      await expect(gateway.readiness(controller.signal)).rejects.toThrow();
    } else if (mode === "changed") {
      post.mockResolvedValue(
        job({ ...command, request_id: crypto.randomUUID() }),
      );
      await expect(
        gateway.enqueue(command, controller.signal),
      ).rejects.toThrow();
    } else if (mode === "duplicate") {
      post.mockResolvedValue({ ...page, items: [job(), job()] });
      await expect(
        gateway.history(subject, controller.signal),
      ).rejects.toThrow();
    } else if (mode === "stale") {
      post.mockResolvedValue(job());
      await expect(
        gateway.update(
          {
            job_id: job().job_id,
            request_id: crypto.randomUUID(),
            expected_sequence: 0,
            action: "retry",
          },
          subject,
          controller.signal,
        ),
      ).rejects.toThrow();
    } else {
      post.mockImplementation(async () => {
        controller.abort();
        return ready;
      });
      await expect(gateway.readiness(controller.signal)).rejects.toThrow();
    }
  },
);
