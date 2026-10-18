import { afterEach, expect, it, vi } from "vitest";
import { apiClient } from "../lib/api-client";
import { passportGateway } from "../lib/persona-passports";
import {
  bindExport,
  parsePackage,
  parseVerification,
} from "../lib/persona-passport-contracts";
import { parseScope } from "../lib/persona-campaign-receipts";
import { parseProduction, productionDraft } from "../lib/persona-production";
import {
  offer,
  packageFixture,
  production,
  status,
  version,
} from "./passport-fixtures";

afterEach(() => vi.restoreAllMocks());
it("preserves legacy scopes while binding distinct production roles and references", () => {
  const { production: ignored, ...legacy } = offer.scope;
  expect(ignored).toEqual(production);
  expect(parseScope(legacy)).toEqual(legacy);
  expect(parseScope(offer.scope).production).toEqual(production);
  expect(productionDraft({ production: "" })).toBeUndefined();
  expect(() =>
    productionDraft({ production: "yes", references: "consent:not-a-uuid" }),
  ).toThrow();
});
it.each([
  { title: " " },
  { role_name: "x".repeat(81) },
  { rights_verified: true },
  {
    supporting_references: [
      { kind: "approved", evidence_id: crypto.randomUUID() },
    ],
  },
])("rejects unsupported production metadata %j", (changes) => {
  expect(() => parseProduction({ ...production, ...changes })).toThrow();
});
it("rejects duplicate or excessive supporting evidence and malformed signed envelopes", () => {
  const ref = { kind: "consent", evidence_id: crypto.randomUUID() };
  expect(() =>
    parseProduction({ ...production, supporting_references: [ref, ref] }),
  ).toThrow();
  expect(() =>
    parseProduction({
      ...production,
      supporting_references: Array.from({ length: 9 }, () => ({
        ...ref,
        evidence_id: crypto.randomUUID(),
      })),
    }),
  ).toThrow();
  for (const changes of [
    { algorithm: "none" },
    { public_key: "browser-key" },
    { signature: "bad" },
    { key_id: "https://arbitrary.test" },
    { payload: { data: "x".repeat(65536) } },
  ]) {
    expect(() => parsePackage({ ...packageFixture(), ...changes })).toThrow();
  }
});
it("binds exports to exact version, scope and unique inspected references", () => {
  const packet = packageFixture();
  expect(() => bindExport(packet, version, offer)).not.toThrow();
  expect(() =>
    bindExport(packet, { ...version, version_id: crypto.randomUUID() }, offer),
  ).toThrow();
  expect(() =>
    bindExport(
      { ...packet, payload: { ...packet.payload, claims: "verified rights" } },
      version,
      offer,
    ),
  ).toThrow();
  expect(() =>
    bindExport(
      { ...packet, payload: { ...packet.payload, references: [] } },
      version,
      offer,
    ),
  ).toThrow();
});
it("separates package integrity from current expiry and forbids permission on altered packages", () => {
  const value = {
    workspace_id: version.workspace_id,
    campaign_id: offer.id,
    integrity: "valid",
    current_status: {
      ...status,
      eligible_for_use: false,
      blocking_reasons: ["expired"],
    },
  };
  expect(
    parseVerification(value, version.workspace_id, offer.id).current_status
      ?.eligible_for_use,
  ).toBe(false);
  expect(() =>
    parseVerification(
      { ...value, integrity: "invalid_signature" },
      version.workspace_id,
      offer.id,
    ),
  ).toThrow();
  expect(() =>
    parseVerification(
      { ...value, workspace_id: crypto.randomUUID() },
      version.workspace_id,
      offer.id,
    ),
  ).toThrow();
  expect(() =>
    parseVerification(
      { ...value, integrity: "valid", current_status: null },
      version.workspace_id,
      offer.id,
    ),
  ).toThrow();
});
it("exposes all four private passport routes with no automatic retry", async () => {
  const ready = {
    workspace_id: version.workspace_id,
    export_available: true,
    verification_available: true,
  };
  const verified = {
    workspace_id: version.workspace_id,
    campaign_id: offer.id,
    integrity: "invalid_signature",
    current_status: null,
  };
  const post = vi
    .spyOn(apiClient, "post")
    .mockResolvedValueOnce(ready)
    .mockResolvedValueOnce({
      workspace_id: version.workspace_id,
      version_id: version.version_id,
      assets: offer.assets,
    })
    .mockResolvedValueOnce(packageFixture())
    .mockResolvedValueOnce(verified);
  const gateway = passportGateway(version.workspace_id),
    signal = new AbortController().signal;
  expect(await gateway.readiness(signal)).toEqual(ready);
  expect(await gateway.assets(version.version_id, signal)).toEqual(
    offer.assets,
  );
  expect(await gateway.export(version, offer, signal)).toEqual(
    packageFixture(),
  );
  expect(await gateway.verify(offer.id, packageFixture(), signal)).toEqual(
    verified,
  );
  expect(post.mock.calls.map((call) => call[0].split("/").at(-1))).toEqual([
    "readiness",
    "assets",
    "export",
    "verify",
  ]);
  expect(
    post.mock.calls.every(
      (call) =>
        call[2]?.retries === 0 &&
        call[2]?.cache === "no-store" &&
        call[2]?.credentials === "same-origin" &&
        call[2]?.redirect === "error",
    ),
  ).toBe(true);
});
it("rejects foreign catalogue data and aborted requests before display", async () => {
  const post = vi.spyOn(apiClient, "post").mockResolvedValue({
    workspace_id: crypto.randomUUID(),
    version_id: version.version_id,
    assets: offer.assets,
  });
  const gateway = passportGateway(version.workspace_id),
    controller = new AbortController();
  await expect(
    gateway.assets(version.version_id, controller.signal),
  ).rejects.toThrow();
  controller.abort();
  await expect(
    gateway.verify(offer.id, packageFixture(), controller.signal),
  ).rejects.toThrow();
  expect(post).toHaveBeenCalledTimes(1);
});
