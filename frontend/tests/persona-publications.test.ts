import { afterEach, expect, it, vi } from "vitest";
import { apiClient } from "../lib/api-client";
import {
  parsePublication,
  publicProjection,
  publicationGateway,
} from "../lib/persona-publications";
import { publicationFixture } from "./evidence-fixtures";
import { offer } from "./passport-fixtures";
afterEach(() => vi.restoreAllMocks());
it.each(["recipient_ref", "evidence_id", "ciphertext", "owner_ref"])(
  "rejects private or unapproved public values %s",
  (key) => {
    const receipt = publicationFixture(),
      values = receipt.package.payload.values as Record<string, unknown>;
    expect(() =>
      publicProjection({
        ...receipt.package,
        payload: {
          ...receipt.package.payload,
          values: { ...values, [key]: "private" },
        },
      }),
    ).toThrow();
  },
);
it("binds public receipt path, workspace and approved fields", async () => {
  const receipt = publicationFixture(),
    post = vi.spyOn(apiClient, "post").mockResolvedValue(receipt);
  const command = {
      request_id: crypto.randomUUID(),
      campaign_id: offer.id,
      fields: ["name", "ai_disclosure"] as ("name" | "ai_disclosure")[],
    },
    signal = new AbortController().signal;
  expect(
    await publicationGateway(receipt.workspace_id).approve(command, signal),
  ).toEqual(receipt);
  expect(post).toHaveBeenCalledWith(
    expect.stringContaining("/publications/approve"),
    command,
    expect.objectContaining({ signal, cache: "no-store", retries: 0 }),
  );
  expect(() =>
    parsePublication(
      { ...receipt, path: "https://foreign.invalid" },
      receipt.workspace_id,
    ),
  ).toThrow();
  post.mockResolvedValue({ ...receipt, workspace_id: crypto.randomUUID() });
  await expect(
    publicationGateway(receipt.workspace_id).approve(command, signal),
  ).rejects.toThrow();
});
