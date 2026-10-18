/** Fictional fixtures; signatures are synthetic and prove no live cryptography. */
import { vi } from "vitest";
import type { PublicationReceipt } from "../lib/persona-publications";
import { personaGateway } from "../lib/persona-gateway";
import { preparedSource } from "./prepared-write-fixtures";
import { gatewayFixture, offer, status, version } from "./passport-fixtures";
import { profile } from "./capture-fixtures";
import {
  publicationFixture,
  publicationGatewayFixture,
} from "./evidence-fixtures";

export function bookletPublicationFixture(): PublicationReceipt {
  const receipt = publicationFixture();
  receipt.package.payload = {
    ...receipt.package.payload,
    version_revision: version.revision,
    valid_from: offer.scope.starts_at,
    valid_until: offer.scope.ends_at,
    values: {
      name: version.content.name,
      ai_disclosure: version.content.ai_disclosure,
    },
  };
  return receipt;
}
export function bookletSource() {
  const source = preparedSource();
  source.gateway = personaGateway(version.workspace_id, async (operation) => {
    if (operation === "campaignOffers")
      return { items: [offer], next_after_id: null };
    if (operation === "campaignStatus") return status;
    throw new Error("Unexpected booklet gateway call");
  });
  source.passports = gatewayFixture();
  source.publications = publicationGatewayFixture();
  source.publications.history = vi.fn(async () => ({
    items: [{ receipt: bookletPublicationFixture(), withdrawn: false }],
    next: null,
  }));
  source.captures = {
    workspaceId: version.workspace_id,
    query: vi.fn(async () => profile),
    thumbnail: vi.fn(
      async () => new Blob(["fictional thumbnail"], { type: "image/png" }),
    ),
  };
  return source;
}
