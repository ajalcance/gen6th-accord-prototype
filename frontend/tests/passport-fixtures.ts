/** Synthetic response fixtures; these strings are not cryptographic acceptance. */
import { vi } from "vitest";
import type { CampaignStatus } from "../lib/persona-contracts";
import type { PassportGateway } from "../lib/persona-passports";
import type { SignedPassport } from "../lib/persona-passport-contracts";
import {
  parseCampaign,
  parseCampaignStatus,
} from "../lib/persona-campaign-receipts";
import { version, campaign } from "./prepared-write-fixtures";
import wire from "./fixtures/persona-wire.json";

export { version };
export const production = {
  title: "Fictional short film",
  episode: "Episode 1",
  role_name: "Captain North",
  adaptation: "Costume change only.",
  supporting_references: [],
};
export const offer = parseCampaign({
  ...campaign,
  scope: { ...campaign.scope, production },
});
export const status: CampaignStatus = parseCampaignStatus({
  ...wire.status,
  receipt: offer,
});
export function packageFixture(): SignedPassport {
  return {
    algorithm: "Ed25519",
    key_id: "synthetic-key",
    signature: "A".repeat(86) + "==",
    payload: {
      format: "accord-persona-passport-v1",
      issued_at: "2026-10-02T04:05:00Z",
      version,
      campaign: offer,
      acceptance_id: wire.decision.id,
      references: [
        {
          portrait_id: "00000000-0000-4000-8000-000000000090",
          source_sha256: "a".repeat(64),
          source_width: 100,
          source_height: 100,
          orientation: 1,
          width: 100,
          height: 100,
          sha256: "b".repeat(64),
          recipe: "rgba-png-1024-v1",
          decoder_version: "synthetic-v1",
          recorded_at: "2026-10-02T04:00:00Z",
        },
      ],
      claims: "creator_statements_and_references_not_independently_verified",
    },
  };
}
export function gatewayFixture(): PassportGateway {
  return {
    workspaceId: version.workspace_id,
    readiness: vi.fn(async () => ({
      workspace_id: version.workspace_id,
      export_available: true,
      verification_available: true,
    })),
    assets: vi.fn(async () => offer.assets),
    export: vi.fn(async () => packageFixture()),
    verify: vi.fn<PassportGateway["verify"]>(async () => ({
      workspace_id: version.workspace_id,
      campaign_id: offer.id,
      integrity: "valid",
      current_status: status,
    })),
  };
}
