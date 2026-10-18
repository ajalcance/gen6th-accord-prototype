import { afterEach, describe, expect, it, vi } from "vitest";
import { personaPreparedWriteTransport } from "../lib/persona-prepared-write-transport";
import {
  personaGateway,
  PersonaDisconnectedError,
} from "../lib/persona-gateway";
import {
  parseSave,
  parseReviewCommand,
  parseOffer,
  parseDecisionCommand,
} from "../lib/persona-commands";
import wire from "./fixtures/persona-wire.json";
import { ContractError } from "../lib/persona-validation";

afterEach(() => vi.unstubAllGlobals());
describe("prepared write transport", () => {
  it("uses four explicit same-origin uncached paths and runtime receipt validation", async () => {
    const responses = [wire.version, wire.review, wire.campaign, wire.decision];
    const fetch = vi.fn<typeof globalThis.fetch>(
      async () =>
        new Response(JSON.stringify(responses.shift()), {
          headers: { "content-type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetch);
    const gateway = personaGateway(
      wire.version.workspace_id,
      personaPreparedWriteTransport(),
    );
    await gateway.save(parseSave(wire.save));
    await gateway.review(parseReviewCommand(wire.reviewCommand));
    await gateway.offer(parseOffer(wire.offer));
    await gateway.decide(parseDecisionCommand(wire.decisionCommand));
    expect(fetch.mock.calls.map(([path]) => path)).toEqual(
      [
        "versions/save",
        "reviews/record",
        "campaigns/offer",
        "campaigns/decide",
      ].map(
        (path) =>
          `/api/workspaces/${wire.version.workspace_id}/personas/${path}`,
      ),
    );
    for (const [, options] of fetch.mock.calls) {
      expect(options).toMatchObject({
        method: "POST",
        credentials: "same-origin",
        mode: "same-origin",
        cache: "no-store",
        redirect: "error",
      });
      expect(new Headers(options?.headers).has("Authorization")).toBe(false);
      expect(JSON.parse(String(options?.body))).not.toHaveProperty("actor_ref");
    }
  });
  it("does not activate reads or add automatic write retries", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>(
      async () => new Response("Unavailable", { status: 503 }),
    );
    vi.stubGlobal("fetch", fetch);
    const gateway = personaGateway(
      wire.version.workspace_id,
      personaPreparedWriteTransport(),
    );
    await expect(gateway.load(wire.version.persona_id)).rejects.toBeInstanceOf(
      PersonaDisconnectedError,
    );
    expect(fetch).not.toHaveBeenCalled();
    await expect(gateway.save(parseSave(wire.save))).rejects.toMatchObject({
      status: 503,
    });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
  it("refuses an old decision receipt when a new decision names that receipt as its predecessor", async () => {
    const reviewGateway = personaGateway(
      wire.version.workspace_id,
      async () => wire.review,
    );
    await expect(
      reviewGateway.review({
        ...parseReviewCommand(wire.reviewCommand),
        expected_previous_id: wire.review.id,
      }),
    ).rejects.toBeInstanceOf(ContractError);
    const decisionGateway = personaGateway(
      wire.version.workspace_id,
      async () => ({
        ...wire.decision,
        id: "00000000-0000-4000-8000-000000000099",
      }),
    );
    await expect(
      decisionGateway.decide({
        ...parseDecisionCommand(wire.decisionCommand),
        expected_previous_id: wire.decision.id,
      }),
    ).rejects.toBeInstanceOf(ContractError);
  });
  it("refuses invalid attribution, foreign receipts and already-cancelled writes", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>(
      async () =>
        new Response(
          JSON.stringify({
            ...wire.version,
            workspace_id: "00000000-0000-4000-8000-000000000099",
          }),
          { headers: { "content-type": "application/json" } },
        ),
    );
    vi.stubGlobal("fetch", fetch);
    const gateway = personaGateway(
      wire.version.workspace_id,
      personaPreparedWriteTransport(),
    );
    await expect(
      gateway.save({
        ...parseSave(wire.save),
        actor_ref: "false",
      } as ReturnType<typeof parseSave>),
    ).rejects.toBeInstanceOf(ContractError);
    expect(fetch).not.toHaveBeenCalled();
    await expect(gateway.save(parseSave(wire.save))).rejects.toBeInstanceOf(
      ContractError,
    );
    const abort = new AbortController();
    abort.abort();
    await expect(
      gateway.save(parseSave(wire.save), abort.signal),
    ).rejects.toMatchObject({ name: "AbortError" });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});
