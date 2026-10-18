import type {
  CampaignReceipt,
  CampaignStatus,
  PersonaVersion,
} from "../../lib/persona-contracts";
import type { SignedPassport } from "../../lib/persona-passport-contracts";
import type { CaptureProfile } from "../../lib/persona-captures";
import type { PublicationReceipt } from "../../lib/persona-publications";
import {
  bookletPublication,
  bookletSignature,
  type BookletSignature,
} from "../../lib/passport-booklet";
import { requireContract } from "../../lib/persona-validation";
import type { SavedPersonaSource } from "./saved-source";

export type BookletRead = {
  profile: CaptureProfile | null;
  portrait: Blob | null;
  status: CampaignStatus | null;
  signature: BookletSignature | null;
  publication: PublicationReceipt | null;
};
export type BookletScope = {
  source: SavedPersonaSource;
  version: PersonaVersion;
  offer: CampaignReceipt | null;
  packet: SignedPassport | null;
};
async function readPortrait(scope: BookletScope, signal: AbortSignal) {
  const { source, version } = scope;
  if (!source.captures) return { profile: null, portrait: null };
  requireContract(source.captures.workspaceId === source.workspaceId);
  const profile = await source.captures.query(
    { upload_id: null, version_id: version.version_id },
    signal,
  );
  requireContract(
    profile.workspace_id === version.workspace_id &&
      profile.version_id === version.version_id,
  );
  const reference = profile.references.find(
    (row) => row.portrait_id === profile.portrait_id,
  );
  const portrait = reference
    ? await source.captures.thumbnail(
        version.version_id,
        reference.portrait_id,
        signal,
      )
    : null;
  return { profile, portrait };
}
async function readPermission(scope: BookletScope, signal: AbortSignal) {
  const { source, version, offer, packet } = scope;
  if (!offer) return { status: null, signature: null };
  const status = await source.gateway.campaignStatus(offer.id, signal);
  requireContract(JSON.stringify(status.receipt) === JSON.stringify(offer));
  if (!packet || !source.passports) return { status, signature: null };
  requireContract(source.passports.workspaceId === source.workspaceId);
  const signature = bookletSignature(packet, version, offer);
  const verification = await source.passports.verify(offer.id, packet, signal);
  requireContract(
    verification.workspace_id === version.workspace_id &&
      verification.campaign_id === offer.id,
  );
  if (verification.integrity !== "valid" || !verification.current_status)
    return { status, signature: null };
  requireContract(
    JSON.stringify(verification.current_status.receipt) ===
      JSON.stringify(offer),
  );
  return { status: verification.current_status, signature };
}
async function readPublication(scope: BookletScope, signal: AbortSignal) {
  const { source, version, offer } = scope;
  if (!offer || !source.publications) return null;
  requireContract(source.publications.workspaceId === source.workspaceId);
  let after: string | null = null;
  const seen = new Set<string>();
  for (let page = 0; page < 10; page++) {
    const history = await source.publications.history(offer.id, after, signal);
    for (const item of history.items) {
      if (item.withdrawn) continue;
      const receipt = bookletPublication(item.receipt, version, offer);
      if (receipt) return receipt;
    }
    if (!history.next) break;
    requireContract(!seen.has(history.next) && !signal.aborted);
    seen.add(history.next);
    after = history.next;
  }
  return null;
}
export async function readBooklet(
  scope: BookletScope,
  signal: AbortSignal,
): Promise<BookletRead> {
  requireContract(scope.source.workspaceId === scope.version.workspace_id);
  if (scope.offer)
    requireContract(
      scope.offer.workspace_id === scope.version.workspace_id &&
        scope.offer.version_id === scope.version.version_id,
    );
  const [portrait, permission] = await Promise.all([
    readPortrait(scope, signal),
    readPermission(scope, signal),
  ]);
  // History is owner-only. Preview readers never need to invoke it.
  const publication = permission.signature
    ? await readPublication(scope, signal)
    : null;
  requireContract(!signal.aborted);
  return { ...portrait, ...permission, publication };
}
