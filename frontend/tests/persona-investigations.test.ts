import { afterEach, expect, it, vi } from "vitest";
import { apiClient } from "../lib/api-client";
import {
  parseInvestigation,
  parseInvestigationPage,
  parseFindings,
} from "../lib/persona-investigation-contracts";
import { investigationGateway } from "../lib/persona-investigations";
import {
  investigationCommand,
  investigationResult,
} from "./investigation-fixtures";

afterEach(() => vi.restoreAllMocks());
it("parses a bound evidence packet even after query pixels expire", () => {
  const packet = investigationResult();
  packet.query.issued_at = "2000-01-01T00:00:00Z";
  packet.query.expires_at = "2000-01-01T00:10:00Z";
  expect(parseInvestigation(packet)).toEqual(packet);
});
it.each([
  { ownership: "verified" },
  { workspace_id: crypto.randomUUID() },
  { gaps: [] },
  { request_id: crypto.randomUUID() },
  { reference_sha256: "bad" },
])("rejects extra conclusions and invalid bindings %j", (changes) => {
  expect(() =>
    parseInvestigation({ ...investigationResult(), ...changes }),
  ).toThrow();
});
it.each([
  { state: "observations", observations: [] },
  {
    state: "observations",
    observations: [
      {
        label: "infringement",
        citations: ["query_image", "approved_reference"],
      },
    ],
  },
  {
    state: "observations",
    observations: [
      { label: "pose_differs", citations: ["query_image", "web"] },
    ],
  },
  { state: "insufficient_evidence", observations: [], confidence: 1 },
])("rejects unsupported model output %j", (raw) =>
  expect(() => parseFindings(raw)).toThrow(),
);
it("binds generate/readiness/history and keeps all requests private with no retries", async () => {
  const packet = investigationResult(),
    intent = investigationCommand();
  const page = {
    workspace_id: packet.workspace_id,
    version_id: packet.version_id,
    items: [packet],
    next_before_ordinal: null,
  };
  const post = vi
    .spyOn(apiClient, "post")
    .mockResolvedValueOnce({
      workspace_id: packet.workspace_id,
      state: "ready",
    })
    .mockResolvedValueOnce(packet)
    .mockResolvedValueOnce(page);
  const gateway = investigationGateway(packet.workspace_id),
    signal = new AbortController().signal;
  expect(await gateway.readiness(signal)).toBe("ready");
  expect(await gateway.generate(intent, signal)).toEqual(packet);
  expect(await gateway.history(packet.version_id, null, signal)).toEqual(page);
  expect(
    post.mock.calls.every(
      (call) =>
        call[2]?.retries === 0 &&
        call[2]?.cache === "no-store" &&
        call[2]?.credentials === "same-origin",
    ),
  ).toBe(true);
  post.mockResolvedValue({ ...packet, version_id: crypto.randomUUID() });
  await expect(gateway.generate(intent, signal)).rejects.toThrow();
});
it("rejects reordered, duplicate, cross-version or unbound history cursors", () => {
  const p = investigationResult();
  const page = {
    workspace_id: p.workspace_id,
    version_id: p.version_id,
    items: [p],
    next_before_ordinal: null,
  };
  for (const changes of [
    { items: [p, p] },
    { next_before_ordinal: 1 },
    { version_id: crypto.randomUUID() },
  ]) {
    expect(() =>
      parseInvestigationPage(
        { ...page, ...changes },
        p.workspace_id,
        p.version_id,
        null,
      ),
    ).toThrow();
  }
  expect(() =>
    parseInvestigationPage(page, p.workspace_id, p.version_id, 1),
  ).toThrow();
});
