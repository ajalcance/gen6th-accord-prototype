import { vi } from "vitest";
import type { EvidenceGateway } from "../lib/persona-evidence";
import type { EvidenceStatus } from "../lib/persona-read-contracts";
import type {
  PublicationGateway,
  PublicationReceipt,
} from "../lib/persona-publications";
import { version } from "./passport-fixtures";

export const evidence: EvidenceStatus = {
  id: "00000000-0000-4000-8000-000000000081",
  workspace_id: version.workspace_id,
  version_id: version.version_id,
  media_type: "text/plain",
  byte_length: 4,
  sha256: "a".repeat(64),
  recorded_at: "2026-10-05T00:00:00Z",
  expires_at: "2026-10-12T00:00:00Z",
  state: "quarantined",
};
export function evidenceFixture(): EvidenceGateway {
  return {
    workspaceId: version.workspace_id,
    readiness: vi.fn(async () => ({
      upload_available: true,
      inspection_available: true,
      download_available: true,
      purge_available: false,
    })),
    upload: vi.fn(async () => evidence),
    inspect: vi.fn(async (): Promise<EvidenceStatus> => ({
      ...evidence,
      state: "clean",
    })),
    download: vi.fn(async () => new Blob(["text"])),
    purge: vi.fn(async (): Promise<EvidenceStatus> => ({
      ...evidence,
      state: "expired",
    })),
  };
}
export function publicationFixture(): PublicationReceipt {
  const id = "00000000-0000-4000-8000-000000000082";
  return {
    workspace_id: version.workspace_id,
    publication_id: id,
    path: `/p/${version.workspace_id}/${id}`,
    package: {
      algorithm: "Ed25519",
      key_id: "synthetic-key",
      signature: "A".repeat(86) + "==",
      payload: {
        format: "accord-public-passport-v1",
        publication_id: id,
        approved_at: "2026-10-05T00:00:00Z",
        valid_from: "2026-10-04T00:00:00Z",
        valid_until: "2026-11-04T00:00:00Z",
        version_revision: 1,
        values: {
          name: "Fictional persona",
          ai_disclosure: "Synthetic fixture",
        },
        claims: "creator_statements_not_independently_verified",
      },
    },
  };
}
export function publicationGatewayFixture(): PublicationGateway {
  return {
    workspaceId: version.workspace_id,
    history: vi.fn(async () => ({ items: [], next: null })),
    approve: vi.fn(async () => publicationFixture()),
    unpublish: vi.fn(async () => publicationFixture()),
  };
}
