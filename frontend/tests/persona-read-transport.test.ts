import { afterEach, describe, expect, it, vi } from "vitest";
import { personaReadTransport } from "../lib/persona-read-transport";
import {
  personaGateway,
  PersonaDisconnectedError,
} from "../lib/persona-gateway";
import wire from "./fixtures/persona-wire.json";

afterEach(() => vi.unstubAllGlobals());
describe("prepared private read HTTP transport", () => {
  it("sends bounded query POSTs without caching, redirects or implicit retries", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>(
      async () =>
        new Response(JSON.stringify(wire.gallery), {
          headers: { "content-type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetch);
    const signal = new AbortController().signal;
    const gateway = personaGateway(
      wire.version.workspace_id,
      personaReadTransport(),
    );
    expect(
      (await gateway.reads.gallery(wire.galleryQuery, signal)).items,
    ).toHaveLength(1);
    const [path, options] = fetch.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(path).toBe(
      `/api/workspaces/${wire.version.workspace_id}/personas/query`,
    );
    expect(options).toMatchObject({
      method: "POST",
      credentials: "same-origin",
      mode: "same-origin",
      cache: "no-store",
      redirect: "error",
    });
    expect(JSON.parse(options.body as string)).toEqual(wire.galleryQuery);
    expect(new Headers(options.headers).has("Authorization")).toBe(false);
  });
  it("loads a version through its own validated query path", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>(
      async () =>
        new Response(JSON.stringify(wire.version), {
          headers: { "content-type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetch);
    await personaGateway(
      wire.version.workspace_id,
      personaReadTransport(),
    ).load(wire.version.persona_id);
    expect(fetch.mock.calls[0][0]).toBe(
      `/api/workspaces/${wire.version.workspace_id}/personas/versions/query`,
    );
  });
  it("does not activate writes or unsupported read operations", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const transport = personaReadTransport();
    await expect(
      transport("save", wire.version.workspace_id, {}),
    ).rejects.toBeInstanceOf(PersonaDisconnectedError);
    await expect(
      transport("reviewHistory", wire.version.workspace_id, {}),
    ).rejects.toBeInstanceOf(PersonaDisconnectedError);
    expect(fetch).not.toHaveBeenCalled();
  });
  it("does not retry failed or cancelled query POSTs", async () => {
    const fetch = vi.fn(
      async () => new Response("Unavailable", { status: 503 }),
    );
    vi.stubGlobal("fetch", fetch);
    const gateway = personaGateway(
      wire.version.workspace_id,
      personaReadTransport(),
    );
    await expect(
      gateway.reads.gallery(wire.galleryQuery),
    ).rejects.toMatchObject({ status: 503 });
    expect(fetch).toHaveBeenCalledTimes(1);
    const abort = new AbortController();
    abort.abort();
    await expect(
      gateway.load(wire.version.persona_id, null, abort.signal),
    ).rejects.toMatchObject({ name: "AbortError" });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});
