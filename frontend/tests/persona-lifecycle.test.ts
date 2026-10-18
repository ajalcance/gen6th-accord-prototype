import { expect, it, vi } from "vitest";
import {
  parseAppendLifecycle,
  parseDossier,
} from "../lib/persona-lifecycle-contracts";
import {
  parseLifecyclePage,
  parseLifecycleProfile,
} from "../lib/persona-lifecycle-reads";
import { lifecycleGateway } from "../lib/persona-lifecycle";
import { parseScope } from "../lib/persona-campaign-receipts";
import { parseProduction } from "../lib/persona-production";
import {
  lifecycleDossier,
  lifecycleProfile,
  lifecycleReceipt,
  id,
} from "./lifecycle-fixtures";

it("rejects client trust, source assertions, empty rights and reversed windows", () => {
  expect(() => parseDossier({ ...lifecycleDossier, verified: true })).toThrow();
  expect(() => parseDossier({ ...lifecycleDossier, rights: [] })).toThrow();
  expect(() =>
    parseDossier({
      ...lifecycleDossier,
      provenance: {
        ...lifecycleDossier.provenance,
        source: "metadata_verified",
      },
    }),
  ).toThrow();
  expect(() =>
    parseDossier({
      ...lifecycleDossier,
      rights: [
        { ...lifecycleDossier.rights[0], ends_at: "2025-01-01T00:00:00Z" },
      ],
    }),
  ).toThrow();
  expect(() =>
    parseAppendLifecycle({
      version_id: lifecycleReceipt.version_id,
      request_id: id(401),
      expected_previous_id: null,
      content: lifecycleDossier,
      actor_ref: "forged",
    }),
  ).toThrow();
});
it("rejects assessment attached to another declaration, duplicate requirements or wrong scope", () => {
  expect(parseLifecycleProfile(lifecycleProfile).requirements).toHaveLength(3);
  const other = structuredClone(lifecycleProfile);
  if (other.requirements[0].assessment?.content.kind === "assessment")
    other.requirements[0].assessment.content.profile_id = id(999);
  expect(() => parseLifecycleProfile(other)).toThrow();
  expect(() =>
    parseLifecycleProfile({
      ...lifecycleProfile,
      requirements: Array(3).fill(lifecycleProfile.requirements[0]),
    }),
  ).toThrow();
  expect(() =>
    parseLifecycleProfile({ ...lifecycleProfile, workspace_id: id(999) }),
  ).toThrow();
});
it("binds append receipts and rejects changed content or outcome after cancellation", async () => {
  const command = {
    version_id: lifecycleReceipt.version_id,
    request_id: lifecycleReceipt.request_id,
    expected_previous_id: null,
    content: lifecycleDossier,
  };
  const transport = vi.fn().mockResolvedValue(lifecycleReceipt),
    controller = new AbortController();
  const gateway = lifecycleGateway(lifecycleReceipt.workspace_id, transport);
  expect(await gateway.append(command, controller.signal)).toEqual(
    lifecycleReceipt,
  );
  transport.mockResolvedValue({
    ...lifecycleReceipt,
    content: {
      ...lifecycleDossier,
      operator: { ...lifecycleDossier.operator, actor_ref: "changed" },
    },
  });
  await expect(gateway.append(command, controller.signal)).rejects.toThrow();
  transport.mockImplementation(async () => {
    controller.abort();
    return lifecycleReceipt;
  });
  await expect(
    gateway.append(command, controller.signal),
  ).rejects.toMatchObject({ name: "AbortError" });
});
it("checks descending history, page bindings and cursor", () => {
  const page = {
    workspace_id: lifecycleReceipt.workspace_id,
    version_id: lifecycleReceipt.version_id,
    items: [lifecycleReceipt],
    next_before_ordinal: 1,
    concerns: [],
  };
  expect(parseLifecyclePage(page).next_before_ordinal).toBe(1);
  expect(() =>
    parseLifecyclePage({ ...page, next_before_ordinal: 2 }),
  ).toThrow();
  expect(() =>
    parseLifecyclePage({
      ...page,
      items: [lifecycleReceipt, lifecycleReceipt],
    }),
  ).toThrow();
});
it("rejects invented approval status and approvals expired at evaluation time", () => {
  const wrong = structuredClone(lifecycleProfile);
  const item = wrong.requirements[0];
  if (item.assessment?.content.kind !== "assessment")
    throw new Error("Fixture assessment required");
  item.assessment.content.decision = "withdrawn";
  expect(() => parseLifecycleProfile(wrong)).toThrow();
  item.assessment.content.decision = "approved";
  item.assessment.content.valid_until = wrong.evaluated_at;
  expect(() => parseLifecycleProfile(wrong)).toThrow();
});
it("preserves legacy production and requires private trials of at most 30 days", () => {
  const legacy = {
    title: "Pilot",
    episode: "One",
    role_name: "Lead",
    adaptation: "Costume",
    supporting_references: [],
  };
  expect(parseProduction(legacy)).toEqual(legacy);
  const production = {
    ...legacy,
    governance_profile_id: lifecycleReceipt.id,
    responsible_operator: "operator",
    use_mode: "trial",
    distribution: "private",
    voice_use: false,
  };
  const scope = {
    name: "Trial",
    recipient_ref: "reviewer",
    asset_ids: [id(401)],
    purpose: "Rehearsal",
    conditions: "Private",
    starts_at: "2026-10-01T00:00:00Z",
    ends_at: "2026-10-31T00:00:00Z",
    production,
  };
  expect(parseScope(scope).production?.use_mode).toBe("trial");
  expect(() =>
    parseScope({ ...scope, ends_at: "2026-11-01T00:00:00Z" }),
  ).toThrow();
  expect(() =>
    parseProduction({ ...production, distribution: "public" }),
  ).toThrow();
});
