import { describe, expect, it, vi } from "vitest";
import { PersonaMutation } from "../lib/persona-mutation";
import { ApiError } from "../lib/api-client";
import { parseSave } from "../lib/persona-commands";
import type { SaveCommand } from "../lib/persona-contracts";
import wire from "./fixtures/persona-wire.json";
import { ContractError } from "../lib/persona-validation";

describe("mutation checkpoint and late-result isolation", () => {
  it("retains uncertainty when a retry loses permission, then resolves the original intent after restoration", async () => {
    const send = vi
      .fn<(command: SaveCommand, signal: AbortSignal) => Promise<unknown>>()
      .mockRejectedValueOnce(new ApiError("outcome unknown", 503))
      .mockRejectedValueOnce(new ApiError("permission lost", 403))
      .mockResolvedValueOnce(wire.version);
    const mutation = new PersonaMutation(send);
    await mutation.submit(parseSave(wire.save));
    await mutation.retry();
    expect(mutation.snapshot.phase).toBe("denied");
    expect(mutation.requiresResolution).toBe(true);
    expect(() => mutation.reset()).toThrow("Resolve");
    await expect(mutation.submit(parseSave(wire.save))).rejects.toThrow(
      "Resolve",
    );
    const restored = new PersonaMutation(send, mutation.checkpoint!);
    expect(restored.canRetry).toBe(true);
    await restored.retry();
    expect(send.mock.calls[0][0]).toEqual(send.mock.calls[2][0]);
    expect(restored.requiresResolution).toBe(false);
  });
  it("treats an invalid response as uncertain but rejects invalid local input before sending", async () => {
    const send = vi
      .fn<(command: SaveCommand, signal: AbortSignal) => Promise<unknown>>()
      .mockRejectedValueOnce(new ContractError())
      .mockResolvedValueOnce(wire.version);
    const mutation = new PersonaMutation(send);
    await mutation.submit(parseSave(wire.save));
    expect(mutation.canRetry).toBe(true);
    expect(() => mutation.reset()).toThrow("Resolve");
    await mutation.retry();
    const local = new PersonaMutation(send, undefined, parseSave);
    expect(
      (await local.submit({ ...parseSave(wire.save), expected_revision: 9 }))
        .phase,
    ).toBe("invalid");
    expect(local.requiresResolution).toBe(false);
    expect(send).toHaveBeenCalledTimes(2);
  });
  it("cancels immediately and permits same-intent retry before the old transport finishes", async () => {
    let finish: (value: unknown) => void = () => {};
    const send = vi
      .fn<(command: SaveCommand, signal: AbortSignal) => Promise<unknown>>()
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            finish = resolve;
          }),
      )
      .mockResolvedValueOnce("new receipt");
    const mutation = new PersonaMutation(send);
    const first = mutation.submit(parseSave(wire.save));
    mutation.cancel();
    expect(mutation.snapshot.phase).toBe("cancelled");
    expect((await mutation.retry()).phase).toBe("succeeded");
    finish("old receipt");
    expect((await first).phase).toBe("cancelled");
    expect(mutation.snapshot).toEqual({
      phase: "succeeded",
      receipt: "new receipt",
    });
    expect(send.mock.calls[0][0]).toEqual(send.mock.calls[1][0]);
  });
  it("restores uncertain intent separately from subsequent editable fields", async () => {
    const send = vi
      .fn<(command: SaveCommand, signal: AbortSignal) => Promise<unknown>>()
      .mockRejectedValueOnce(new ApiError("unavailable", 503))
      .mockResolvedValueOnce(wire.version);
    const original = new PersonaMutation(send),
      command = parseSave(wire.save);
    await original.submit(command);
    const checkpoint = original.checkpoint!;
    command.content.name = "Unsaved edit";
    const restored = new PersonaMutation(send, checkpoint);
    await expect(restored.submit(command)).rejects.toThrow("Resolve");
    await restored.retry();
    const retryOnly = new PersonaMutation(send, checkpoint);
    expect(() => retryOnly.reset()).toThrow("Resolve");
    await retryOnly.retry();
    expect(send.mock.calls.at(-1)?.[0]).toEqual(wire.save);
  });
  it("retains conflict/denial without retry authority and never checkpoints a server receipt", async () => {
    const failed = new PersonaMutation<SaveCommand, unknown>(async () => {
      throw new ApiError("private", 403);
    });
    await failed.submit(parseSave(wire.save));
    const restored = new PersonaMutation(
      async () => wire.version,
      failed.checkpoint!,
    );
    await expect(restored.retry()).rejects.toThrow("review");
    restored.reset();
    expect(restored.intent).toBeNull();
    await restored.submit(parseSave(wire.save));
    expect(restored.checkpoint).toBeNull();
  });
});
