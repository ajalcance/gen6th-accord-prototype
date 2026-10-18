import { afterEach, expect, it, vi } from "vitest";
import { ApiError, apiClient } from "../lib/api-client";
import { assistantGateway, parseBrief } from "../lib/persona-assistant";
import { wireBrief } from "./assistant-fixtures";
import { version } from "./prepared-write-fixtures";

afterEach(() => vi.restoreAllMocks());

it("accepts the exact server contract", () => {
  expect(parseBrief(wireBrief)).toEqual(wireBrief);
  expect(
    parseBrief({
      ...wireBrief,
      state: "insufficient_information",
      gaps: [],
      questions: [],
    }).gaps,
  ).toEqual([]);
});
it.each([
  { extra: "field" },
  { state: "approved" },
  { revision: "1" },
  { revision: 0 },
  { persona_id: "not-a-uuid" },
  { summary: "" },
  { summary: "x".repeat(451) },
  { summary: "See https://example.invalid" },
  { summary: "<b>approved</b>" },
  { summary: "Use `code`" },
  { gaps: ["line\u0007bell"] },
  { gaps: ["a", "b", "c", "d", "e"] },
  { gaps: [""] },
  { questions: ["x".repeat(161)] },
  { questions: [42] },
  { generated_at: "yesterday" },
  { notice: "" },
  { model: "" },
])("rejects an invalid or unsafe brief %j", (changes) => {
  expect(() => parseBrief({ ...wireBrief, ...changes })).toThrow();
});
it("rejects a brief with a missing field", () => {
  const rest: Record<string, unknown> = { ...wireBrief };
  delete rest.notice;
  expect(() => parseBrief(rest)).toThrow();
});
it("posts privately, once, with the exact version and no actor or content", async () => {
  const post = vi.spyOn(apiClient, "post").mockResolvedValue(wireBrief);
  const result = await assistantGateway(version.workspace_id).brief(
    version.persona_id,
    version.revision,
    new AbortController().signal,
  );
  expect(result.summary).toBe(wireBrief.summary);
  const [path, body, options] = post.mock.calls[0];
  expect(path).toBe(
    `/api/workspaces/${version.workspace_id}/personas/assistant/brief`,
  );
  expect(body).toEqual({
    persona_id: version.persona_id,
    revision: version.revision,
  });
  expect(options).toMatchObject({
    retries: 0,
    cache: "no-store",
    redirect: "error",
    credentials: "same-origin",
    mode: "same-origin",
  });
});
it.each([
  { name: "another performer", changes: { persona_id: crypto.randomUUID() } },
  { name: "another revision", changes: { revision: version.revision + 1 } },
])("rejects a result for $name before display", async ({ changes }) => {
  vi.spyOn(apiClient, "post").mockResolvedValue({ ...wireBrief, ...changes });
  await expect(
    assistantGateway(version.workspace_id).brief(
      version.persona_id,
      version.revision,
      new AbortController().signal,
    ),
  ).rejects.toThrow();
});
it("rejects an aborted request and invalid arguments without calling the server", async () => {
  const post = vi.spyOn(apiClient, "post").mockResolvedValue(wireBrief);
  const gateway = assistantGateway(version.workspace_id);
  const controller = new AbortController();
  controller.abort();
  await expect(
    gateway.brief(version.persona_id, 1, controller.signal),
  ).rejects.toThrow();
  await expect(
    gateway.brief("nope", 1, new AbortController().signal),
  ).rejects.toThrow();
  await expect(
    gateway.brief(version.persona_id, 0, new AbortController().signal),
  ).rejects.toThrow();
  expect(post).not.toHaveBeenCalled();
  expect(() => assistantGateway("nope")).toThrow();
});
it("surfaces a rate limit as a failure, never as a partial brief", async () => {
  vi.spyOn(apiClient, "post").mockRejectedValue(new ApiError("429", 429));
  await expect(
    assistantGateway(version.workspace_id).brief(
      version.persona_id,
      null,
      new AbortController().signal,
    ),
  ).rejects.toBeInstanceOf(ApiError);
});
