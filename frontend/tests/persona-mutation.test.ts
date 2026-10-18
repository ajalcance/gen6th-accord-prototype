import { describe, expect, it, vi } from "vitest";
import wire from "./fixtures/persona-wire.json";
import { ApiError } from "../lib/api-client";
import { PersonaMutation } from "../lib/persona-mutation";
import { parseSave } from "../lib/persona-commands";
import type { SaveCommand } from "../lib/persona-contracts";

describe("persona mutation recovery", () => {
  it("retries the identical request despite subsequent draft edits", async () => {
    const send = vi
      .fn<(command: SaveCommand, signal: AbortSignal) => Promise<unknown>>()
      .mockRejectedValueOnce(new ApiError("unavailable", 503))
      .mockResolvedValue(wire.version);
    const mutation = new PersonaMutation(send);
    const command = parseSave(wire.save);
    expect((await mutation.submit(command)).phase).toBe("retryable");
    command.content.name = "New unsaved draft";
    expect((await mutation.retry()).phase).toBe("succeeded");
    expect(send.mock.calls[0][0]).toEqual(send.mock.calls[1][0]);
    expect(send.mock.calls[1][0].content.name).toBe(wire.save.content.name);
    expect(command.content.name).toBe("New unsaved draft");
  });

  it.each([
    [409, "conflict"],
    [401, "denied"],
    [403, "denied"],
    [422, "failed"],
  ])(
    "preserves intent and requires review for status %s",
    async (status, phase) => {
      const mutation = new PersonaMutation<SaveCommand, unknown>(async () => {
        throw new ApiError("server detail must not leak", Number(status));
      });
      expect((await mutation.submit(parseSave(wire.save))).phase).toBe(phase);
      expect(mutation.intent).toEqual(wire.save);
      await expect(mutation.retry()).rejects.toThrow("review");
    },
  );

  it("shows pending, prevents double submission and resolves cancelled writes through same-intent retry", async () => {
    let finish: (result: unknown) => void = () => {};
    const send = vi
      .fn<(command: SaveCommand, signal: AbortSignal) => Promise<unknown>>()
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            finish = resolve;
          }),
      )
      .mockResolvedValue(wire.version);
    const mutation = new PersonaMutation(send);
    const pending = mutation.submit(parseSave(wire.save));
    expect(mutation.snapshot.phase).toBe("pending");
    await expect(mutation.submit(parseSave(wire.save))).rejects.toThrow(
      "already pending",
    );
    mutation.cancel();
    finish(wire.version);
    expect((await pending).phase).toBe("cancelled");
    expect((await mutation.retry()).phase).toBe("succeeded");
    expect(send.mock.calls[0][0]).toEqual(send.mock.calls[1][0]);
  });
});
