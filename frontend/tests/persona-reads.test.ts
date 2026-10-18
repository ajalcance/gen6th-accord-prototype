import { describe, expect, it, vi } from "vitest";
import wire from "./fixtures/persona-wire.json";
import {
  personaGateway,
  PersonaDisconnectedError,
  type PersonaTransport,
} from "../lib/persona-gateway";
import {
  parseGalleryPage,
  parseGalleryQuery,
  parseHistoryQuery,
  parseDecisionPage,
} from "../lib/persona-pages";
import { parseReview } from "../lib/persona-receipts";
import { parseWorkflowEvidence } from "../lib/persona-evidence-receipts";
import { ContractError } from "../lib/persona-validation";

const workspace = wire.version.workspace_id;
const historyQuery = { before_ordinal: null, limit: 20 };

describe("prepared read adapters", () => {
  it("reads gallery, history and evidence through backend-compatible wire examples", async () => {
    const responses: Record<string, unknown> = {
      gallery: wire.gallery,
      reviewHistory: wire.reviewHistory,
      campaignHistory: wire.campaignHistory,
      evidenceStatus: wire.evidenceStatus,
      workflowEvidence: wire.workflowEvidence,
    };
    const transport = vi.fn<PersonaTransport>(
      async (operation) => responses[operation],
    );
    const reads = personaGateway(workspace, transport).reads;
    expect((await reads.gallery(wire.galleryQuery)).items).toEqual([
      wire.version,
    ]);
    expect(
      (await reads.reviewHistory(wire.version.version_id, historyQuery)).items,
    ).toEqual([wire.review]);
    expect(
      (await reads.campaignHistory(wire.campaign.id, historyQuery)).items,
    ).toEqual([wire.decision]);
    expect((await reads.evidenceStatus(wire.evidenceStatus.id)).state).toBe(
      "quarantined",
    );
    const evidence = await reads.workflowEvidence(wire.review.id, "review");
    expect(evidence.audit_state).toBe("pending");
    expect(evidence).not.toHaveProperty("verified");
    expect(transport.mock.calls.every(([, scope]) => scope === workspace)).toBe(
      true,
    );
  });

  it("read operations are also disconnected by default", async () => {
    await expect(
      personaGateway(workspace).reads.gallery(wire.galleryQuery),
    ).rejects.toBeInstanceOf(PersonaDisconnectedError);
  });

  it.each([
    { ...wire.gallery, workspace_id: wire.version.persona_id },
    { ...wire.gallery, items: [wire.version, wire.version] },
    { ...wire.gallery, next_after_persona_id: wire.version.persona_id },
    {
      ...wire.gallery,
      items: [{ ...wire.version, workspace_id: wire.version.persona_id }],
    },
  ])("rejects mismatched gallery pages %j", (page) => {
    expect(() => parseGalleryPage(page, workspace, wire.galleryQuery)).toThrow(
      ContractError,
    );
  });

  it("rejects a cursor pointing backwards and overlarge pages", () => {
    expect(() =>
      parseGalleryPage(wire.gallery, workspace, {
        ...wire.galleryQuery,
        after_persona_id: wire.version.persona_id,
      }),
    ).toThrow(ContractError);
    expect(() =>
      parseGalleryPage(
        { ...wire.gallery, items: [wire.version, wire.version] },
        workspace,
        { ...wire.galleryQuery, limit: 1 },
      ),
    ).toThrow(ContractError);
  });

  it.each([
    { items: [wire.review, wire.review], next_before_ordinal: null },
    { items: [wire.review], next_before_ordinal: 99 },
    { items: [], next_before_ordinal: 1 },
  ])("rejects duplicate or inconsistent history pages %j", (page) => {
    expect(() =>
      parseDecisionPage(page, historyQuery, parseReview, () => true),
    ).toThrow(ContractError);
  });

  it("rejects history for another version or campaign", async () => {
    const reads = personaGateway(
      workspace,
      async () => wire.reviewHistory,
    ).reads;
    await expect(
      reads.reviewHistory(wire.version.persona_id, historyQuery),
    ).rejects.toBeInstanceOf(ContractError);
    const campaigns = personaGateway(
      workspace,
      async () => wire.campaignHistory,
    ).reads;
    await expect(
      campaigns.campaignHistory(wire.version.persona_id, historyQuery),
    ).rejects.toBeInstanceOf(ContractError);
  });

  it.each([
    { ...wire.workflowEvidence, cold_event_present: false },
    { ...wire.workflowEvidence, audit_state: "entry_present" },
    { ...wire.workflowEvidence, audit_sequence: 1 },
    { ...wire.workflowEvidence, audit_entry_hash: "f".repeat(64) },
  ])("does not upgrade incomplete audit references %j", (page) => {
    expect(() => parseWorkflowEvidence(page)).toThrow(ContractError);
  });

  it("rejects a decision anchor for a different requested record kind", async () => {
    const reads = personaGateway(
      workspace,
      async () => wire.workflowEvidence,
    ).reads;
    await expect(
      reads.workflowEvidence(wire.review.id, "campaign_offer"),
    ).rejects.toBeInstanceOf(ContractError);
  });

  it("rejects private fields in an evidence status response", async () => {
    const reads = personaGateway(workspace, async () => ({
      ...wire.evidenceStatus,
      ciphertext: "not public",
    })).reads;
    await expect(
      reads.evidenceStatus(wire.evidenceStatus.id),
    ).rejects.toBeInstanceOf(ContractError);
  });

  it("validates bounded read inputs before sending", () => {
    expect(() =>
      parseGalleryQuery({ ...wire.galleryQuery, limit: 101 }),
    ).toThrow(ContractError);
    expect(() =>
      parseGalleryQuery({ ...wire.galleryQuery, actor_ref: "creator-a" }),
    ).toThrow(ContractError);
    expect(() =>
      parseHistoryQuery({ ...historyQuery, before_ordinal: 0 }),
    ).toThrow(ContractError);
  });

  it("discards cancelled read results even if the transport ignores cancellation", async () => {
    const abort = new AbortController();
    const reads = personaGateway(workspace, async () => {
      abort.abort();
      return wire.gallery;
    }).reads;
    await expect(
      reads.gallery(wire.galleryQuery, abort.signal),
    ).rejects.toMatchObject({ name: "AbortError" });
  });
});
