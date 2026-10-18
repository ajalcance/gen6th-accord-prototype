import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiClient, request } from "../lib/api-client";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("api-client", () => {
  it.each([
    new Headers({ "X-Request-ID": "fixture-request" }),
    [["X-Request-ID", "fixture-request"]] as [string, string][],
  ])("preserves supported header representations", async (headers) => {
    const fetchMock = vi.fn(async () => jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    await request("/health", { headers });
    const options = vi.mocked(fetch).mock.calls[0][1];
    expect(new Headers(options?.headers).get("X-Request-ID")).toBe(
      "fixture-request",
    );
  });
  it("does not send a request already cancelled by the caller", async () => {
    const abort = new AbortController();
    abort.abort();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      request("/health", { signal: abort.signal }),
    ).rejects.toMatchObject({ name: "AbortError" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("forwards caller cancellation and never retries it", async () => {
    const abort = new AbortController();
    const fetchMock = vi.fn(
      (_path: string, init: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init.signal?.addEventListener("abort", () =>
            reject(new DOMException("cancelled", "AbortError")),
          );
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const result = request("/health", { signal: abort.signal });
    abort.abort();
    await expect(result).rejects.toMatchObject({ name: "AbortError" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("returns the parsed JSON body on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse({ status: "ok" })),
    );
    await expect(apiClient.get<{ status: string }>("/health")).resolves.toEqual(
      { status: "ok" },
    );
  });

  it("throws ApiError carrying the status and body on a non-2xx response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse({ detail: "nope" }, 422)),
    );
    const error = await apiClient.get("/thing").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(422);
    expect((error as ApiError).body).toEqual({ detail: "nope" });
  });

  it("retries an idempotent GET on a 5xx and succeeds", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: "boom" }, 503))
      .mockResolvedValueOnce(jsonResponse({ status: "ok" }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(request("/health", { retries: 1 })).resolves.toEqual({
      status: "ok",
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("does NOT retry a POST — a duplicate write is worse than a failure", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ detail: "boom" }, 503));
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiClient.post("/things", { a: 1 })).rejects.toBeInstanceOf(
      ApiError,
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not retry a non-retryable status such as 404", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({ detail: "missing" }, 404),
    );
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiClient.get("/missing")).rejects.toBeInstanceOf(ApiError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
