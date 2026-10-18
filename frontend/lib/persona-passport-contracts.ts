/** Packages use reviewed server trust keys. Browser parsing does not verify a signature. */
import type {
  CampaignReceipt,
  CampaignStatus,
  PersonaVersion,
} from "./persona-contracts";
import {
  parseCampaign,
  parseCampaignStatus,
} from "./persona-campaign-receipts";
import { parseVersion } from "./persona-receipts";
import { parseCapture } from "./persona-captures";
import {
  choice,
  list,
  object,
  requireContract,
  text,
  timestamp,
  uuid,
} from "./persona-validation";
export type SignedPassport = {
  algorithm: "Ed25519";
  key_id: string;
  payload: Record<string, unknown>;
  signature: string;
};
export type PassportReadiness = {
  workspace_id: string;
  export_available: boolean;
  verification_available: boolean;
};
export type PassportVerification = {
  workspace_id: string;
  campaign_id: string;
  integrity:
    | "valid"
    | "invalid_signature"
    | "untrusted_key"
    | "invalid_package"
    | "binding_mismatch";
  current_status: CampaignStatus | null;
};
export const PACKAGE_LIMIT = 64 * 1024;

export function parsePackage(value: unknown): SignedPassport {
  const row = object(value, ["algorithm", "key_id", "payload", "signature"]);
  requireContract(
    row.payload !== null &&
      typeof row.payload === "object" &&
      !Array.isArray(row.payload),
  );
  const key = text(row.key_id, 240);
  requireContract(row.key_id === key);
  requireContract(
    /^[A-Za-z0-9_./-]+$/.test(key) &&
      typeof row.signature === "string" &&
      /^[A-Za-z0-9+/]{86}==$/.test(row.signature),
  );
  requireContract(
    new TextEncoder().encode(JSON.stringify(value)).length <=
      PACKAGE_LIMIT - 128,
  );
  return {
    algorithm: choice(row.algorithm, ["Ed25519"]),
    key_id: key,
    payload: row.payload as Record<string, unknown>,
    signature: row.signature,
  };
}
export function parseReadiness(
  value: unknown,
  workspace: string,
): PassportReadiness {
  const row = object(value, [
    "workspace_id",
    "export_available",
    "verification_available",
  ]);
  requireContract(
    uuid(row.workspace_id) === workspace &&
      typeof row.export_available === "boolean" &&
      typeof row.verification_available === "boolean",
  );
  return {
    workspace_id: workspace,
    export_available: row.export_available,
    verification_available: row.verification_available,
  };
}
export function parseVerification(
  value: unknown,
  workspace: string,
  campaign: string,
): PassportVerification {
  const row = object(value, [
    "workspace_id",
    "campaign_id",
    "integrity",
    "current_status",
  ]);
  const integrity = choice(row.integrity, [
    "valid",
    "invalid_signature",
    "untrusted_key",
    "invalid_package",
    "binding_mismatch",
  ]);
  const status =
    row.current_status === null
      ? null
      : parseCampaignStatus(row.current_status);
  requireContract(
    uuid(row.workspace_id) === workspace &&
      uuid(row.campaign_id) === campaign &&
      (integrity === "valid") === (status !== null),
  );
  if (status)
    requireContract(
      status.receipt.workspace_id === workspace &&
        status.receipt.id === campaign,
    );
  return {
    workspace_id: workspace,
    campaign_id: campaign,
    integrity,
    current_status: status,
  };
}
export function bindExport(
  package_: SignedPassport,
  version: PersonaVersion,
  offer: CampaignReceipt,
): void {
  const payload = object(package_.payload, [
    "format",
    "issued_at",
    "version",
    "campaign",
    "acceptance_id",
    "references",
    "claims",
  ]);
  requireContract(
    payload.format === "accord-persona-passport-v1" &&
      payload.claims ===
        "creator_statements_and_references_not_independently_verified",
  );
  requireContract(
    JSON.stringify(parseVersion(payload.version)) === JSON.stringify(version) &&
      JSON.stringify(parseCampaign(payload.campaign)) === JSON.stringify(offer),
  );
  uuid(payload.acceptance_id);
  timestamp(payload.issued_at);
  const refs = list(payload.references, parseCapture, 8, 1);
  requireContract(
    new Set(refs.map((item) => item.portrait_id)).size === refs.length,
  );
}
