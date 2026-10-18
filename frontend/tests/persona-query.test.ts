import { describe, expect, it } from "vitest";
import { PersonaQuery } from "../lib/persona-query";
import { ApiError } from "../lib/api-client";
import { ContractError } from "../lib/persona-validation";
import { PersonaDisconnectedError } from "../lib/persona-gateway";

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

describe("read state isolation", () => {
  it("clears old results while loading and publishes completed reads", async () => {
    const query = new PersonaQuery<string>();
    const states: string[] = [];
    const unsubscribe = query.subscribe(() =>
      states.push(query.snapshot().phase),
    );
    await query.run(async () => "first");
    const waiting = deferred<string>();
    const read = query.run(() => waiting.promise);
    expect(query.snapshot()).toEqual({ phase: "loading" });
    waiting.resolve("second");
    await read;
    expect(query.snapshot()).toEqual({ phase: "ready", value: "second" });
    unsubscribe();
    query.clear();
    expect(states).toEqual(["loading", "ready", "loading", "ready"]);
  });
  it("rejects late results from replaced queries even when transport ignores abort", async () => {
    const query = new PersonaQuery<string>();
    const old = deferred<string>();
    const earlier = query.run(() => old.promise);
    await query.run(async () => "current");
    old.resolve("stale private data");
    await earlier;
    expect(query.snapshot()).toEqual({ phase: "ready", value: "current" });
  });
  it("stops cancelled reads and retries only after an explicit action", async () => {
    const query = new PersonaQuery<string>();
    const waiting = deferred<string>();
    let calls = 0;
    let signal: AbortSignal | undefined;
    const read = query.run((value) => {
      calls++;
      signal = value;
      return waiting.promise;
    });
    query.cancel();
    expect(signal?.aborted).toBe(true);
    waiting.resolve("late");
    await read;
    expect(query.snapshot().phase).toBe("cancelled");
    expect(calls).toBe(1);
    await query.retry();
    expect(calls).toBe(2);
    expect(query.snapshot()).toEqual({ phase: "ready", value: "late" });
  });
  it.each([401, 403])(
    "clears denied records and prohibits automatic retry for %s",
    async (status) => {
      const query = new PersonaQuery<string>();
      await query.run(async () => "private record");
      await query.run(async () => {
        throw new ApiError("private detail", status);
      });
      expect(query.snapshot().phase).toBe("denied");
      expect(query.snapshot()).not.toHaveProperty("value");
      expect(() => query.retry()).toThrow();
    },
  );
  it.each([
    [new ContractError(), "invalid"],
    [new PersonaDisconnectedError(), "disconnected"],
    [new ApiError("private detail", 503), "unavailable"],
    [new ApiError("private detail", 0), "unavailable"],
  ])("sanitizes failed reads %j", async (error, phase) => {
    const query = new PersonaQuery<string>();
    await query.run(async () => {
      throw error;
    });
    expect(query.snapshot().phase).toBe(phase);
    expect(JSON.stringify(query.snapshot())).not.toContain("private detail");
  });
  it("clear removes the result and retry closure before leaving the list", async () => {
    const query = new PersonaQuery<string>();
    await query.run(async () => "record");
    query.clear();
    expect(query.snapshot().phase).toBe("idle");
    expect(() => query.retry()).toThrow();
  });
});
