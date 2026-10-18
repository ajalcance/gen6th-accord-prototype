import { afterEach, expect, it, vi } from "vitest";
import { apiClient, ApiError } from "../lib/api-client";
import { PersonaQuery } from "../lib/persona-query";
import { similarityGateway } from "../lib/persona-similarity";
import {
  parseQueryReceipt,
  parseSimilarityPage,
} from "../lib/persona-similarity-contracts";
import { preparePhoto } from "../lib/persona-photos";
import {
  command,
  queryImage,
  queryReceipt,
  similarityPage,
} from "./similarity-fixtures";

afterEach(() => vi.restoreAllMocks());
it("parses bounded detection and similarity without private vectors", () => {
  const receipt = queryReceipt(),
    page = similarityPage();
  expect(parseQueryReceipt(receipt)).toEqual(receipt);
  expect(parseSimilarityPage(page)).toEqual(page);
});
it.each([
  { width: 1025 },
  { faces: [{ ...queryReceipt().faces[0], x: 1020 }] },
  { expires_at: "2000-01-01T00:00:00Z" },
  { state: "no_face" },
  { vectors: [[1]] },
])("rejects invalid query receipts %j", (changes) => {
  expect(() => parseQueryReceipt({ ...queryReceipt(), ...changes })).toThrow();
});
it.each([
  { vectors: [[1]] },
  { has_more: true },
  { compatible_count: 129 },
  { items: [similarityPage().items[0], similarityPage().items[0]] },
  { state: "no_confident_match" },
  { representation: null },
  { face_index: 10 },
  { items: [{ ...similarityPage().items[0], face_cosine: NaN }] },
  { items: [{ ...similarityPage().items[0], whole_cosine: 1.01 }] },
  {
    items: [
      {
        ...similarityPage().items[0],
        version: {
          ...similarityPage().items[0].version,
          workspace_id: "00000000-0000-4000-8000-000000000001",
        },
      },
    ],
  },
])("rejects contradictory or unbound ranked pages %j", (changes) => {
  expect(() =>
    parseSimilarityPage({ ...similarityPage(), ...changes }),
  ).toThrow();
});
it("uses private explicit POST and binds prepare/search/clear/readiness", async () => {
  const upload = await preparePhoto(queryImage()),
    receipt = {
      ...queryReceipt(),
      query_id: upload.request_id,
      source_sha256: upload.sha256,
    };
  const post = vi
    .spyOn(apiClient, "post")
    .mockResolvedValueOnce(receipt)
    .mockResolvedValueOnce(similarityPage())
    .mockResolvedValueOnce({
      workspace_id: receipt.workspace_id,
      query_id: receipt.query_id,
      closed: true,
    })
    .mockResolvedValueOnce({
      workspace_id: receipt.workspace_id,
      state: "calibration_required",
      policy_id: null,
    });
  const gateway = similarityGateway(receipt.workspace_id),
    signal = new AbortController().signal;
  expect(await gateway.prepare(upload, signal)).toEqual(receipt);
  expect(await gateway.search(command, signal)).toEqual(similarityPage());
  await gateway.clear(receipt.query_id, signal);
  expect((await gateway.readiness(signal)).state).toBe("calibration_required");
  expect(
    post.mock.calls.every(
      (call) =>
        call[2]?.retries === 0 &&
        call[2]?.cache === "no-store" &&
        call[2]?.credentials === "same-origin",
    ),
  ).toBe(true);
  post.mockResolvedValue({
    ...similarityPage(),
    query_id: crypto.randomUUID(),
  });
  await expect(gateway.search(command, signal)).rejects.toThrow();
});
it("expires reads without enabling retry of an old query", async () => {
  const query = new PersonaQuery();
  await query.run(async () => {
    throw new ApiError("Expired", 410);
  });
  expect(query.snapshot().phase).toBe("expired");
  expect(() => query.retry()).toThrow(/fresh request/);
});
