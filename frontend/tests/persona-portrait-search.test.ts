import { afterEach, expect, it, vi } from "vitest";
import { apiClient } from "../lib/api-client";
import {
  parsePortraitSearch,
  portraitSearchGateway,
} from "../lib/persona-portrait-search";
import { ContractError } from "../lib/persona-validation";
import wire from "./fixtures/persona-wire.json";

const command = {
  request_id: "00000000-0000-4000-8000-000000000090",
  media_type: "image/png" as const,
  byte_length: 9,
  sha256: "a".repeat(64),
  data: "c3ludGhldGlj",
};
const page = {
  workspace_id: wire.version.workspace_id,
  request_id: command.request_id,
  sha256: command.sha256,
  method: "exact_file_sha256",
  items: [wire.version],
  has_more: false,
};
afterEach(() => vi.restoreAllMocks());

it.each([
  { method: "face_identity" },
  { sha256: "invalid" },
  { has_more: true },
  { items: [wire.version, wire.version] },
  { items: [{ ...wire.version, workspace_id: crypto.randomUUID() }] },
  { claimed_probability: 1 },
])("rejects malformed or misleading search receipts %j", (change) => {
  expect(() => parsePortraitSearch({ ...page, ...change })).toThrow(
    ContractError,
  );
});

it("uses the real private transport and binds receipt to bytes, request and workspace", async () => {
  const post = vi.spyOn(apiClient, "post").mockResolvedValue(page);
  const signal = new AbortController().signal;
  const result = await portraitSearchGateway(page.workspace_id).search(
    command,
    signal,
  );
  expect(result.items[0].version_id).toBe(wire.version.version_id);
  expect(post).toHaveBeenCalledWith(
    `/api/workspaces/${page.workspace_id}/personas/photos/search`,
    command,
    expect.objectContaining({
      signal,
      cache: "no-store",
      credentials: "same-origin",
      retries: 0,
      redirect: "error",
    }),
  );
});

it.each(["workspace_id", "request_id", "sha256"] as const)(
  "rejects a receipt for a different %s",
  async (field) => {
    const wrong = field === "sha256" ? "b".repeat(64) : crypto.randomUUID();
    vi.spyOn(apiClient, "post").mockResolvedValue({
      ...page,
      [field]: wrong,
      items: field === "workspace_id" ? [] : page.items,
    });
    await expect(
      portraitSearchGateway(page.workspace_id).search(
        command,
        new AbortController().signal,
      ),
    ).rejects.toThrow(ContractError);
  },
);

it("rejects a late response after cancellation", async () => {
  const controller = new AbortController();
  vi.spyOn(apiClient, "post").mockImplementation(async () => {
    controller.abort();
    return page;
  });
  await expect(
    portraitSearchGateway(page.workspace_id).search(command, controller.signal),
  ).rejects.toThrow(ContractError);
});
