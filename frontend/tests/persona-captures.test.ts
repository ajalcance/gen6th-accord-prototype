import { afterEach, expect, it, vi } from "vitest";
import { Blob as NativeBlob } from "node:buffer";
import { apiClient } from "../lib/api-client";
import {
  captureGateway,
  parseCapture,
  parseCaptureProfile,
} from "../lib/persona-captures";
import { parseSave } from "../lib/persona-commands";
import { ContractError } from "../lib/persona-validation";
import { capture, profile } from "./capture-fixtures";
import { version } from "./prepared-write-fixtures";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
it.each([
  { width: 1025 },
  { orientation: 9 },
  { source_width: 4096, source_height: 4096 },
  { width: true },
  { recorded_at: "2026-10-05T12:00:00" },
  { ciphertext: "private" },
  { recipe: "face-v1" },
  { source_width: 10 },
])("rejects malformed capture provenance %j", (change) => {
  expect(() => parseCapture({ ...capture, ...change })).toThrow(ContractError);
});

it("fetches only a version-bound reference thumbnail with bounded private transport", async () => {
  vi.stubGlobal("Blob", NativeBlob);
  const png = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]);
  const fetch = vi.fn<typeof globalThis.fetch>(
    async () => new Response(png, { headers: { "content-type": "image/png" } }),
  );
  vi.stubGlobal("fetch", fetch);
  const gateway = captureGateway(profile.workspace_id),
    signal = new AbortController().signal;
  expect(
    (await gateway.thumbnail(version.version_id, capture.portrait_id, signal))
      .size,
  ).toBe(8);
  expect(fetch).toHaveBeenCalledWith(
    `/api/workspaces/${profile.workspace_id}/personas/photos/versions/${version.version_id}/references/${capture.portrait_id}/thumbnail`,
    expect.objectContaining({
      cache: "no-store",
      credentials: "same-origin",
      redirect: "error",
    }),
  );
  fetch.mockImplementation(
    async () =>
      new Response("not-png", { headers: { "content-type": "image/png" } }),
  );
  await expect(
    gateway.thumbnail(version.version_id, capture.portrait_id, signal),
  ).rejects.toThrow(ContractError);
});
it.each([
  { recognition: "matched" },
  { references: [capture, capture] },
  { upload_id: capture.portrait_id },
  { portrait_id: crypto.randomUUID() },
  { references: Array(9).fill(capture) },
  { owner_ref: "forged" },
])("rejects inconsistent reference profile %j", (change) => {
  expect(() => parseCaptureProfile({ ...profile, ...change })).toThrow(
    ContractError,
  );
});
it("uses private POST without retries and binds the requested version", async () => {
  const post = vi.spyOn(apiClient, "post").mockResolvedValue(profile);
  const command = { upload_id: null, version_id: profile.version_id };
  const signal = new AbortController().signal;
  const gateway = captureGateway(profile.workspace_id);
  expect(await gateway.query(command, signal)).toEqual(profile);
  expect(post).toHaveBeenCalledWith(
    expect.stringContaining("/photos/capture/query"),
    command,
    expect.objectContaining({
      signal,
      retries: 0,
      cache: "no-store",
      credentials: "same-origin",
      redirect: "error",
    }),
  );
  post.mockResolvedValue({ ...profile, version_id: crypto.randomUUID() });
  await expect(gateway.query(command, signal)).rejects.toThrow(ContractError);
});
it("rejects cancelled and foreign workspace metadata", async () => {
  const post = vi
    .spyOn(apiClient, "post")
    .mockResolvedValue({ ...profile, workspace_id: crypto.randomUUID() });
  const gateway = captureGateway(profile.workspace_id),
    command = { upload_id: null, version_id: profile.version_id };
  await expect(
    gateway.query(command, new AbortController().signal),
  ).rejects.toThrow(ContractError);
  const abort = new AbortController();
  abort.abort();
  post.mockResolvedValue(profile);
  await expect(gateway.query(command, abort.signal)).rejects.toThrow(
    ContractError,
  );
});
it("retains explicit clear and ordered references in normalized save intent", () => {
  const intent = {
    request_id: crypto.randomUUID(),
    content: version.content,
    persona_id: version.persona_id,
    expected_revision: 1,
  };
  expect(parseSave(intent).references).toBeUndefined();
  expect(
    parseSave({ ...intent, references: { action: "replace", upload_ids: [] } })
      .references?.upload_ids,
  ).toEqual([]);
  expect(() =>
    parseSave({
      ...intent,
      references: { action: "keep", upload_ids: [capture.portrait_id] },
    }),
  ).toThrow(ContractError);
  expect(() =>
    parseSave({
      ...intent,
      references: {
        action: "replace",
        upload_ids: Array(2).fill(capture.portrait_id),
      },
    }),
  ).toThrow(ContractError);
});
