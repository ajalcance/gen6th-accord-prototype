import type { DecisionReceipt, ReviewReceipt } from "./persona-contracts";
import type {
  DecisionPage,
  GalleryPage,
  GalleryQuery,
  HistoryQuery,
} from "./persona-read-contracts";
import { parseVersion } from "./persona-receipts";
import {
  integer,
  list,
  object,
  requireContract,
  uuid,
} from "./persona-validation";

export function parseGalleryQuery(value: unknown): GalleryQuery {
  const row = object(value, ["after_persona_id", "limit", "search"]);
  const limit = integer(row.limit);
  requireContract(limit <= 100 && typeof row.search === "string");
  const search = row.search.trim();
  requireContract([...search].length <= 80);
  return {
    after_persona_id:
      row.after_persona_id === null ? null : uuid(row.after_persona_id),
    limit,
    search,
  };
}
export function parseHistoryQuery(value: unknown): HistoryQuery {
  const row = object(value, ["before_ordinal", "limit"]);
  const limit = integer(row.limit);
  requireContract(limit <= 100);
  return {
    before_ordinal:
      row.before_ordinal === null ? null : integer(row.before_ordinal),
    limit,
  };
}
export function parseGalleryPage(
  value: unknown,
  workspace: string,
  query: GalleryQuery,
): GalleryPage {
  const row = object(value, ["workspace_id", "items", "next_after_persona_id"]);
  requireContract(uuid(row.workspace_id) === workspace);
  const items = list(row.items, parseVersion, query.limit);
  requireContract(
    items.every(
      (item, index) =>
        item.workspace_id === workspace &&
        (index === 0 || item.persona_id > items[index - 1].persona_id) &&
        (query.after_persona_id === null ||
          item.persona_id > query.after_persona_id),
    ),
  );
  const next =
    row.next_after_persona_id === null ? null : uuid(row.next_after_persona_id);
  requireContract(
    next === null ||
      (items.length === query.limit && next === items.at(-1)?.persona_id),
  );
  return { workspace_id: workspace, items, next_after_persona_id: next };
}
export function parseDecisionPage<T extends ReviewReceipt | DecisionReceipt>(
  value: unknown,
  query: HistoryQuery,
  parse: (item: unknown) => T,
  belongs: (item: T) => boolean,
): DecisionPage<T> {
  const row = object(value, ["items", "next_before_ordinal"]);
  const items = list(row.items, parse, query.limit);
  requireContract(
    items.every(
      (item, index) =>
        belongs(item) &&
        (index === 0 || item.ordinal < items[index - 1].ordinal) &&
        (query.before_ordinal === null || item.ordinal < query.before_ordinal),
    ),
  );
  requireContract(new Set(items.map((item) => item.id)).size === items.length);
  const next =
    row.next_before_ordinal === null ? null : integer(row.next_before_ordinal);
  requireContract(
    next === null ||
      (items.length === query.limit && next === items.at(-1)?.ordinal),
  );
  return { items, next_before_ordinal: next };
}
