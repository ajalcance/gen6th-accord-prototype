import { describe, expect, it, vi } from "vitest";
import wire from "./fixtures/persona-wire.json";
import {
  personaGateway,
  PersonaDisconnectedError,
  type PersonaTransport,
  type PersonaOperation,
} from "../lib/persona-gateway";
import {
  parseDecisionCommand,
  parseOffer,
  parseReviewCommand,
  parseSave,
} from "../lib/persona-commands";
import { parseCampaignStatus } from "../lib/persona-campaign-receipts";
import { ContractError } from "../lib/persona-validation";

describe("prepared persona connection", () => {
  it("stays disconnected without an explicitly injected transport", async () => {
    await expect(
      personaGateway(wire.version.workspace_id).save(parseSave(wire.save)),
    ).rejects.toBeInstanceOf(PersonaDisconnectedError);
  });

  it("validates the System Capture through campaign journey using shared backend wire examples", async () => {
    const responses: Partial<Record<PersonaOperation, unknown>> = {
      save: wire.version,
      load: wire.version,
      review: wire.review,
      offer: wire.campaign,
      decide: wire.decision,
      campaignStatus: wire.status,
    };
    const transport = vi.fn<PersonaTransport>(
      async (operation) => responses[operation],
    );
    const gateway = personaGateway(wire.version.workspace_id, transport);
    const version = await gateway.save(parseSave(wire.save));
    expect(await gateway.load(version.persona_id, 1)).toEqual(version);
    const review = await gateway.review(parseReviewCommand(wire.reviewCommand));
    const offer = await gateway.offer(
      parseOffer({ ...wire.offer, review_id: review.id }),
    );
    const decision = await gateway.decide(
      parseDecisionCommand({ ...wire.decisionCommand, campaign_id: offer.id }),
    );
    expect(decision.decision).toBe("accepted");
    expect((await gateway.campaignStatus(offer.id)).eligible_for_use).toBe(
      true,
    );
    expect(transport.mock.calls.map(([operation]) => operation)).toEqual([
      "save",
      "load",
      "review",
      "offer",
      "decide",
      "campaignStatus",
    ]);
    expect(
      transport.mock.calls.every(
        ([, workspace, command]) =>
          workspace === version.workspace_id &&
          !("actor_ref" in (command as object)),
      ),
    ).toBe(true);
  });

  it.each([
    { ...wire.version, workspace_id: wire.version.persona_id },
    { ...wire.version, revision: 2 },
    { ...wire.version, content: { ...wire.version.content, fixture: "false" } },
    {
      ...wire.version,
      content: { ...wire.version.content, name: "Different record" },
    },
    { ...wire.version, private_key: "unexpected field" },
  ])("rejects mismatched or malformed save receipt %j", async (response) => {
    const gateway = personaGateway(
      wire.version.workspace_id,
      async () => response,
    );
    await expect(gateway.save(parseSave(wire.save))).rejects.toBeInstanceOf(
      ContractError,
    );
  });

  it("rejects authority fields before invoking transport", () => {
    expect(() => parseSave({ ...wire.save, actor_ref: "creator-a" })).toThrow(
      ContractError,
    );
    expect(() =>
      parseReviewCommand({ ...wire.reviewCommand, kind: "human" }),
    ).toThrow(ContractError);
  });

  it.each([
    { ...wire.status, latest_decision: null },
    { ...wire.status, evaluated_at: wire.campaign.scope.ends_at },
    { ...wire.status, blocking_reasons: ["revoked"] },
    {
      ...wire.status,
      latest_decision: { ...wire.decision, actor_ref: "creator-a" },
    },
    {
      ...wire.status,
      latest_decision: {
        ...wire.decision,
        campaign_id: wire.version.persona_id,
      },
    },
  ])(
    "never treats an inconsistent acceptance as eligibility %j",
    (response) => {
      expect(() => parseCampaignStatus(response)).toThrow(ContractError);
    },
  );

  it("cancellation prevents late responses from appearing successful", async () => {
    const abort = new AbortController();
    const gateway = personaGateway(wire.version.workspace_id, async () => {
      abort.abort();
      return wire.version;
    });
    await expect(
      gateway.save(parseSave(wire.save), abort.signal),
    ).rejects.toMatchObject({ name: "AbortError" });
  });
});
