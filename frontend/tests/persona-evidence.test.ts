// @vitest-environment node
import { afterEach, expect, it, vi } from "vitest";
import { evidenceGateway, prepareEvidence } from "../lib/persona-evidence";
import { evidence } from "./evidence-fixtures";

afterEach(() => vi.unstubAllGlobals());
const signal = () => new AbortController().signal;
it("uploads only on command, binds digest and version, and never retries", async () => {
  const file = new File(["text"], "private.txt", { type: "text/plain" });
  const fetcher = vi.fn();
  vi.stubGlobal("fetch", fetcher);
  const command = await prepareEvidence(file, evidence.version_id);
  expect(fetcher).not.toHaveBeenCalled();
  const row = { ...evidence, sha256: command.digest };
  fetcher.mockResolvedValue(new Response(JSON.stringify(row)));
  expect(
    await evidenceGateway(row.workspace_id).upload(command, signal()),
  ).toEqual(row);
  expect(fetcher.mock.calls[0][1]).toMatchObject({
    credentials: "same-origin",
    cache: "no-store",
    redirect: "error",
    body: file,
    headers: {
      "X-Request-ID": command.requestId,
      "X-Content-SHA256": command.digest,
    },
  });
  fetcher.mockResolvedValue(
    new Response(JSON.stringify({ ...row, version_id: crypto.randomUUID() })),
  );
  await expect(
    evidenceGateway(row.workspace_id).upload(command, signal()),
  ).rejects.toThrow();
  expect(fetcher).toHaveBeenCalledTimes(2);
});
it.each(["clean", "digest", "oversize", "short", "foreign", "cancelled"])(
  "private download rejects %s faults before releasing bytes",
  async (fault) => {
    const command = await prepareEvidence(
      new File(["text"], "x", { type: "text/plain" }),
      evidence.version_id,
    );
    const row = {
      ...evidence,
      sha256: command.digest,
      state: "clean" as const,
    };
    const fetcher = vi.fn(
      async () =>
        new Response(fault === "digest" ? "evil" : "text", {
          headers: {
            "Content-Type": "application/octet-stream",
            "X-Content-SHA256": row.sha256,
          },
        }),
    );
    vi.stubGlobal("fetch", fetcher);
    const controller = new AbortController();
    if (fault === "cancelled") controller.abort();
    const input = {
      ...row,
      ...(fault === "clean" ? { state: "quarantined" as const } : {}),
      ...(fault === "oversize" ? { byte_length: 3 } : {}),
      ...(fault === "short" ? { byte_length: 5 } : {}),
      ...(fault === "foreign" ? { workspace_id: crypto.randomUUID() } : {}),
    };
    await expect(
      evidenceGateway(row.workspace_id).download(input, controller.signal),
    ).rejects.toThrow();
    if (["clean", "foreign"].includes(fault))
      expect(fetcher).not.toHaveBeenCalled();
  },
);
it("releases only the exact inspected private bytes", async () => {
  const command = await prepareEvidence(
    new File(["text"], "x", { type: "text/plain" }),
    evidence.version_id,
  );
  const row = { ...evidence, sha256: command.digest, state: "clean" as const };
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response("text", {
          headers: {
            "Content-Type": "application/octet-stream",
            "X-Content-SHA256": row.sha256,
          },
        }),
    ),
  );
  expect(
    await (
      await evidenceGateway(row.workspace_id).download(row, signal())
    ).text(),
  ).toBe("text");
});
