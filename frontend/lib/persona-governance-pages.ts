/** Strict, bounded discovery. Every returned reference belongs to the selected record. */
import type { CampaignReceipt, PersonaVersion } from "./persona-contracts";
import type { EvidenceStatus } from "./persona-read-contracts";
import { parseCampaign } from "./persona-campaign-receipts";
import { parseEvidenceStatus } from "./persona-evidence-receipts";
import { parseVersion } from "./persona-receipts";
import {
  integer,
  list,
  object,
  requireContract,
  uuid,
} from "./persona-validation";

export type VersionHistoryQuery = {
  before_revision: number | null;
  limit: number;
};
export type ObjectQuery = { after_id: string | null; limit: number };
export type VersionPage = {
  items: PersonaVersion[];
  next_before_revision: number | null;
};
export type ObjectPage<T> = { items: T[]; next_after_id: string | null };

export function versionQuery(value: unknown): VersionHistoryQuery {
  const row = object(value, ["before_revision", "limit"]);
  const limit = integer(row.limit);
  requireContract(limit <= 100);
  return {
    before_revision:
      row.before_revision === null ? null : integer(row.before_revision),
    limit,
  };
}
export function objectQuery(value: unknown): ObjectQuery {
  const row = object(value, ["after_id", "limit"]);
  const limit = integer(row.limit);
  requireContract(limit <= 100);
  return { after_id: row.after_id === null ? null : uuid(row.after_id), limit };
}
export function versionPage(
  raw: unknown,
  workspace: string,
  persona: string,
  query: VersionHistoryQuery,
): VersionPage {
  const row = object(raw, ["items", "next_before_revision"]);
  const items = list(row.items, parseVersion, query.limit);
  requireContract(
    items.every(
      (item, index) =>
        item.workspace_id === workspace &&
        item.persona_id === persona &&
        (index === 0 || item.revision < items[index - 1].revision) &&
        (query.before_revision === null ||
          item.revision < query.before_revision),
    ),
  );
  requireContract(
    new Set(items.map((item) => item.version_id)).size === items.length,
  );
  const next =
    row.next_before_revision === null
      ? null
      : integer(row.next_before_revision);
  requireContract(
    next === null ||
      (items.length === query.limit && next === items.at(-1)?.revision),
  );
  return { items, next_before_revision: next };
}
export function objectPage<
  T extends { id: string; workspace_id: string; version_id: string },
>(
  raw: unknown,
  workspace: string,
  version: string,
  query: ObjectQuery,
  parse: (raw: unknown) => T,
): ObjectPage<T> {
  const row = object(raw, ["items", "next_after_id"]);
  const items = list(row.items, parse, query.limit);
  requireContract(
    items.every(
      (item, index) =>
        item.workspace_id === workspace &&
        item.version_id === version &&
        (index === 0 || item.id > items[index - 1].id) &&
        (query.after_id === null || item.id > query.after_id),
    ),
  );
  const next = row.next_after_id === null ? null : uuid(row.next_after_id);
  requireContract(
    next === null ||
      (items.length === query.limit && next === items.at(-1)?.id),
  );
  return { items, next_after_id: next };
}
export const campaignPage = (
  raw: unknown,
  workspace: string,
  version: string,
  query: ObjectQuery,
): ObjectPage<CampaignReceipt> =>
  objectPage(raw, workspace, version, query, parseCampaign);
export const evidencePage = (
  raw: unknown,
  workspace: string,
  version: string,
  query: ObjectQuery,
): ObjectPage<EvidenceStatus> =>
  objectPage(raw, workspace, version, query, parseEvidenceStatus);
