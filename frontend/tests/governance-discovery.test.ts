import { describe, expect, it, vi } from "vitest";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import { ContractError } from "../lib/persona-validation";
import wire from "./fixtures/persona-wire.json";

const versionQuery = { before_revision: null, limit: 20 };
const objectQuery = { after_id: null, limit: 20 };
function client(raw: unknown) {
  return personaGateway(
    wire.version.workspace_id,
    vi.fn<PersonaTransport>(async () => raw),
  );
}
describe("bounded governance discovery", () => {
  it("accepts exact selected versions, offers and metadata-only evidence", async () => {
    expect(
      (
        await client({
          items: [wire.version],
          next_before_revision: null,
        }).governance.versions(wire.version.persona_id, versionQuery)
      ).items,
    ).toHaveLength(1);
    expect(
      (
        await client({
          items: [wire.campaign],
          next_after_id: null,
        }).governance.campaigns(wire.version.version_id, objectQuery)
      ).items,
    ).toHaveLength(1);
    expect(
      (
        await client({
          items: [wire.evidenceStatus],
          next_after_id: null,
        }).governance.evidence(wire.version.version_id, objectQuery)
      ).items,
    ).toHaveLength(1);
  });
  it.each(["workspace_id", "persona_id"])(
    "rejects version history bound to another %s",
    async (field) => {
      await expect(
        client({
          items: [{ ...wire.version, [field]: wire.campaign.id }],
          next_before_revision: null,
        }).governance.versions(wire.version.persona_id, versionQuery),
      ).rejects.toBeInstanceOf(ContractError);
    },
  );
  it.each(["workspace_id", "version_id"])(
    "rejects foreign campaign and evidence %s",
    async (field) => {
      await expect(
        client({
          items: [{ ...wire.campaign, [field]: wire.version.persona_id }],
          next_after_id: null,
        }).governance.campaigns(wire.version.version_id, objectQuery),
      ).rejects.toBeInstanceOf(ContractError);
      await expect(
        client({
          items: [{ ...wire.evidenceStatus, [field]: wire.version.persona_id }],
          next_after_id: null,
        }).governance.evidence(wire.version.version_id, objectQuery),
      ).rejects.toBeInstanceOf(ContractError);
    },
  );
  it("rejects duplicate references, wrong order and dishonest continuation cursors", async () => {
    for (const items of [
      [wire.version, wire.version],
      [
        wire.version,
        { ...wire.version, revision: 2, version_id: wire.campaign.id },
      ],
    ])
      await expect(
        client({ items, next_before_revision: null }).governance.versions(
          wire.version.persona_id,
          versionQuery,
        ),
      ).rejects.toBeInstanceOf(ContractError);
    await expect(
      client({
        items: [wire.version],
        next_before_revision: 1,
      }).governance.versions(wire.version.persona_id, versionQuery),
    ).rejects.toBeInstanceOf(ContractError);
    await expect(
      client({
        items: [wire.evidenceStatus, wire.evidenceStatus],
        next_after_id: null,
      }).governance.evidence(wire.version.version_id, objectQuery),
    ).rejects.toBeInstanceOf(ContractError);
    await expect(
      client({
        items: [wire.campaign],
        next_after_id: wire.campaign.id,
      }).governance.campaigns(wire.version.version_id, objectQuery),
    ).rejects.toBeInstanceOf(ContractError);
  });
  it("enforces exclusive cursor bounds and maximum request/response size", async () => {
    await expect(
      client({
        items: [wire.version],
        next_before_revision: null,
      }).governance.versions(wire.version.persona_id, {
        before_revision: 1,
        limit: 20,
      }),
    ).rejects.toBeInstanceOf(ContractError);
    await expect(
      client({
        items: [wire.evidenceStatus],
        next_after_id: null,
      }).governance.evidence(wire.version.version_id, {
        after_id: wire.evidenceStatus.id,
        limit: 20,
      }),
    ).rejects.toBeInstanceOf(ContractError);
    const transport = vi.fn<PersonaTransport>();
    await expect(
      personaGateway(wire.version.workspace_id, transport).governance.versions(
        wire.version.persona_id,
        { before_revision: null, limit: 101 },
      ),
    ).rejects.toBeInstanceOf(ContractError);
    expect(transport).not.toHaveBeenCalled();
  });
  it("rejects private material and invented authority in metadata", async () => {
    await expect(
      client({
        items: [{ ...wire.evidenceStatus, key_id: "synthetic-key-reference" }],
        next_after_id: null,
      }).governance.evidence(wire.version.version_id, objectQuery),
    ).rejects.toBeInstanceOf(ContractError);
  });
  it("honors cancellation before discovering any reference", async () => {
    const transport = vi.fn<PersonaTransport>(),
      abort = new AbortController();
    abort.abort();
    await expect(
      personaGateway(wire.version.workspace_id, transport).governance.campaigns(
        wire.version.version_id,
        objectQuery,
        abort.signal,
      ),
    ).rejects.toMatchObject({ name: "AbortError" });
    expect(transport).not.toHaveBeenCalled();
  });
});
