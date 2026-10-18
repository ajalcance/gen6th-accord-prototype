import { afterEach, describe, expect, it, vi } from "vitest";
import { governancePreview } from "./legacy-passport/governance-preview-transport";
import { saveRecoveryPreview } from "./legacy-passport/governance-save-preview";
import {
  EXAMPLE_CAMPAIGN,
  EXAMPLE_DECISIONS,
  EXAMPLE_EVIDENCE,
  EXAMPLE_PERSONA,
  EXAMPLE_REVIEWS,
  EXAMPLE_VERSIONS,
  exampleId,
} from "./legacy-passport/governance-fixtures";
import { PersonaMutation } from "../lib/persona-mutation";
import type { PersonaVersion, SaveCommand } from "../lib/persona-contracts";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
const command: SaveCommand = {
  request_id: exampleId(400),
  persona_id: EXAMPLE_PERSONA,
  expected_revision: 2,
  content: EXAMPLE_VERSIONS[0].content,
};

describe("isolated governance contract examples", () => {
  it("validates all immutable versions and binds review history to its exact version", async () => {
    const gateway = governancePreview();
    for (const row of EXAMPLE_VERSIONS)
      expect(await gateway.load(EXAMPLE_PERSONA, row.revision)).toEqual(row);
    expect(await gateway.load(EXAMPLE_PERSONA)).toEqual(EXAMPLE_VERSIONS[0]);
    const page = await gateway.reads.reviewHistory(
      EXAMPLE_VERSIONS[1].version_id,
      { before_ordinal: null, limit: 1 },
    );
    expect(page.items).toEqual([EXAMPLE_REVIEWS[0]]);
    expect(page.next_before_ordinal).toBe(2);
    const older = await gateway.reads.reviewHistory(
      EXAMPLE_VERSIONS[1].version_id,
      { before_ordinal: 2, limit: 1 },
    );
    expect(older.items).toEqual([EXAMPLE_REVIEWS[1]]);
    expect(older.next_before_ordinal).toBeNull();
    expect(
      (
        await gateway.reads.reviewHistory(EXAMPLE_VERSIONS[0].version_id, {
          before_ordinal: null,
          limit: 1,
        })
      ).items,
    ).toEqual([]);
  });
  it("keeps historical acceptance separate from current blocked use", async () => {
    const gateway = governancePreview();
    const status = await gateway.campaignStatus(EXAMPLE_CAMPAIGN.id);
    expect(status.eligible_for_use).toBe(false);
    expect(status.blocking_reasons).toEqual(["revoked", "stale_version"]);
    const page = await gateway.reads.campaignHistory(EXAMPLE_CAMPAIGN.id, {
      before_ordinal: null,
      limit: 2,
    });
    expect(page.items).toEqual(EXAMPLE_DECISIONS.slice(0, 2));
    expect(page.next_before_ordinal).toBe(2);
    expect(
      (
        await gateway.reads.campaignHistory(EXAMPLE_CAMPAIGN.id, {
          before_ordinal: 2,
          limit: 2,
        })
      ).items,
    ).toEqual([EXAMPLE_DECISIONS[2]]);
  });
  it("validates all four metadata-only evidence states and pending versus present audit entries", async () => {
    const gateway = governancePreview();
    for (const row of EXAMPLE_EVIDENCE)
      expect(await gateway.reads.evidenceStatus(row.id)).toEqual(row);
    for (const row of EXAMPLE_REVIEWS) {
      const evidence = await gateway.reads.workflowEvidence(row.id, "review");
      expect(evidence.anchor.actor_ref).toBe(row.reviewer_ref);
      expect(evidence.audit_state).toBe(
        row.ordinal === 1 ? "entry_present" : "pending",
      );
    }
    for (const row of EXAMPLE_DECISIONS)
      expect(
        (await gateway.reads.workflowEvidence(row.id, "campaign_decision"))
          .anchor.record_id,
      ).toBe(row.id);
  });
  it("returns an empty history and rejects unknown objects, writes and mismatched kinds without HTTP", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const gateway = governancePreview();
    expect(
      (
        await governancePreview("empty").reads.reviewHistory(
          EXAMPLE_VERSIONS[1].version_id,
          { before_ordinal: null, limit: 1 },
        )
      ).items,
    ).toEqual([]);
    await expect(gateway.load(exampleId(999))).rejects.toThrow();
    await expect(
      gateway.reads.reviewHistory(exampleId(999), {
        before_ordinal: null,
        limit: 1,
      }),
    ).rejects.toThrow();
    await expect(
      gateway.reads.evidenceStatus(exampleId(999)),
    ).rejects.toThrow();
    await expect(
      gateway.reads.workflowEvidence(
        EXAMPLE_REVIEWS[0].id,
        "campaign_decision",
      ),
    ).rejects.toThrow();
    await expect(gateway.save(command)).rejects.toThrow(/not connected/);
    expect(fetch).not.toHaveBeenCalled();
  });
  it.each(["unavailable", "denied"] as const)(
    "models %s and aborts without returning example records",
    async (condition) => {
      const gateway = governancePreview(condition);
      await expect(gateway.load(EXAMPLE_PERSONA)).rejects.toThrow();
      const controller = new AbortController();
      controller.abort();
      await expect(
        gateway.load(EXAMPLE_PERSONA, null, controller.signal),
      ).rejects.toMatchObject({ name: "AbortError" });
    },
  );
});

describe("recovery examples preserve retry intent", () => {
  it.each(["conflict", "denied"] as const)(
    "requires review after %s",
    async (scenario) => {
      const gateway = saveRecoveryPreview(scenario);
      const mutation = new PersonaMutation<SaveCommand, PersonaVersion>(
        (body, signal) => gateway.save(body, signal),
      );
      expect((await mutation.submit(command)).phase).toBe(scenario);
      await expect(mutation.retry()).rejects.toThrow(/review/);
      expect(mutation.intent).toEqual(command);
    },
  );
  it("retries the exact original snapshot after uncertain outcome without real writes", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const gateway = saveRecoveryPreview("unavailable");
    const send = vi.fn((body: SaveCommand, signal: AbortSignal) =>
      gateway.save(body, signal),
    );
    const mutation = new PersonaMutation<SaveCommand, PersonaVersion>(send);
    const draft = structuredClone(command);
    expect((await mutation.submit(draft)).phase).toBe("retryable");
    draft.content.name = "Edited after submitting";
    expect((await mutation.retry()).phase).toBe("succeeded");
    expect(send.mock.calls[1][0]).toEqual(command);
    expect(fetch).not.toHaveBeenCalled();
  });
  it("aborts the pending example and resolves its same intent on explicit retry", async () => {
    const gateway = saveRecoveryPreview("unavailable");
    const mutation = new PersonaMutation<SaveCommand, PersonaVersion>(
      (body, signal) => gateway.save(body, signal),
    );
    const pending = mutation.submit(command);
    mutation.cancel();
    expect((await pending).phase).toBe("cancelled");
    expect((await mutation.retry()).phase).toBe("succeeded");
    expect(mutation.intent).toEqual(command);
  });
});
