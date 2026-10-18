/** Display projection only. Parsing a package does not verify its signature. */
import type { CampaignReceipt, PersonaVersion } from "./persona-contracts";
import {
  bindExport,
  parsePackage,
  type SignedPassport,
} from "./persona-passport-contracts";
import { parseCapture } from "./persona-captures";
import {
  parsePublication,
  publicProjection,
  type PublicationReceipt,
} from "./persona-publications";
import { list, timestamp } from "./persona-validation";
import { passportQr } from "./passport-qr";

export type BookletSignature = {
  key: string;
  issued: string;
  references: number;
};
export function bookletReference(offer: CampaignReceipt | null): string {
  return offer
    ? `AC-${offer.id.replaceAll("-", "").slice(-8).toUpperCase()}`
    : "Not assigned";
}
export function bookletSignature(
  packet: SignedPassport,
  version: PersonaVersion,
  offer: CampaignReceipt,
): BookletSignature {
  const parsed = parsePackage(packet);
  bindExport(parsed, version, offer);
  return {
    key: parsed.key_id.split("/").slice(-2).join("/"),
    issued: timestamp(parsed.payload.issued_at),
    references: list(parsed.payload.references, parseCapture, 8, 1).length,
  };
}
export function bookletPublication(
  receipt: PublicationReceipt,
  version: PersonaVersion,
  offer: CampaignReceipt,
): PublicationReceipt | null {
  const parsed = parsePublication(receipt, version.workspace_id);
  const projection = publicProjection(parsed.package);
  if (
    projection.revision !== version.revision ||
    projection.values.name !== version.content.name ||
    projection.values.ai_disclosure !== version.content.ai_disclosure ||
    Date.parse(projection.from) !== Date.parse(offer.scope.starts_at) ||
    Date.parse(projection.until) !== Date.parse(offer.scope.ends_at)
  )
    return null;
  return parsed;
}
export function bookletShare(path: string | null, origin: string) {
  if (!path || !origin) return null;
  try {
    const url = new URL(path, origin);
    if (url.origin !== origin || !url.pathname.startsWith("/p/")) return null;
    return { url: url.href, modules: passportQr(url.href) };
  } catch {
    return null;
  }
}
export function bookletMachineLine(
  version: PersonaVersion,
  offer: CampaignReceipt | null,
): string {
  const name = version.content.name
    .normalize("NFKD")
    .replace(/[^A-Za-z0-9 ]/g, "")
    .trim()
    .replaceAll(" ", "_")
    .toUpperCase();
  return `ACCORD::${name || "PERFORMER"}::REV_${version.revision}\n${offer ? `OFFER::${offer.id}` : "REGISTRATION::NO_OFFER"}`;
}
