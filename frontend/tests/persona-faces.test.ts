import { afterEach, expect, it, vi } from "vitest";
import { apiClient } from "../lib/api-client";
import { faceGateway, parseFaceResult } from "../lib/persona-faces";
import { detected } from "./face-fixtures";

afterEach(() => vi.restoreAllMocks());
it("parses bounded version-bound face detection without identity probability", () => {
  expect(parseFaceResult(detected)).toEqual(detected);
});
it.each([
  { ...detected, vectors: [[1]] },
  { ...detected, selected: 0 },
  { ...detected, width: 50 },
  { ...detected, state: "represented" },
  { ...detected, faces: [{ ...detected.faces[0], confidence: Infinity }] },
  { ...detected, faces: [{ ...detected.faces[0], index: 1 }] },
])("rejects malformed or mismatched face state %j", (row) => {
  expect(() => parseFaceResult(row)).toThrow();
});
it("uses same-origin bounded explicit POST and binds query/processing responses", async () => {
  const post = vi
    .spyOn(apiClient, "post")
    .mockResolvedValueOnce({
      workspace_id: detected.workspace_id,
      version_id: detected.version_id,
      portrait_id: detected.portrait_id,
      latest: detected,
      provider_ready: true,
    })
    .mockResolvedValueOnce(detected);
  const gateway = faceGateway(detected.workspace_id),
    signal = new AbortController().signal;
  const subject = {
    version_id: detected.version_id,
    portrait_id: detected.portrait_id,
  };
  expect((await gateway.query(subject, signal)).latest).toEqual(detected);
  await expect(
    gateway.process(
      {
        ...subject,
        request_id: "00000000-0000-4000-8000-000000000099",
        generation_id: null,
        face_index: null,
      },
      signal,
    ),
  ).rejects.toThrow();
  expect(post.mock.calls[0][2]).toMatchObject({
    credentials: "same-origin",
    mode: "same-origin",
    cache: "no-store",
    retries: 0,
    timeoutMs: 10000,
  });
  expect(post.mock.calls[1][2]).toMatchObject({ timeoutMs: 75000, retries: 0 });
});
