import type { Draft } from "./fixture-data";
import { readDraft } from "./fixture-data";
import type { ConsoleRecord } from "./console-types";

export const STORAGE_KEY = "accord-h1-console-v2";
const DEFAULT_DISCLOSURE =
  "Fictional synthetic character concept. No real person or generation log.";
type StoredRecord = Pick<ConsoleRecord, "id" | "variant" | "draft">;

function boundedDraft(value: unknown): Draft | null {
  if (
    !value ||
    typeof value !== "object" ||
    !("name" in value) ||
    !("bio" in value) ||
    !("contribution" in value)
  )
    return null;
  if (
    typeof value.name !== "string" ||
    typeof value.bio !== "string" ||
    typeof value.contribution !== "string"
  )
    return null;
  const disclosure =
    "disclosure" in value ? value.disclosure : DEFAULT_DISCLOSURE;
  if (typeof disclosure !== "string") return null;
  return {
    name: value.name.slice(0, 80),
    bio: value.bio.slice(0, 500),
    contribution: value.contribution.slice(0, 500),
    disclosure: disclosure.slice(0, 500),
  };
}

function storedRecord(value: unknown, index: number): StoredRecord {
  if (
    !value ||
    typeof value !== "object" ||
    !("draft" in value) ||
    !("id" in value) ||
    !("variant" in value)
  )
    throw new Error("Invalid fixture storage");
  const expectedId = ["nova", "iris", "arden"][index] ?? `local-${index + 1}`;
  if (
    value.id !== expectedId ||
    typeof value.variant !== "number" ||
    !Number.isInteger(value.variant) ||
    value.variant < 0 ||
    value.variant > 2
  )
    throw new Error("Invalid fixture storage");
  const draft = boundedDraft(value.draft);
  if (!draft) throw new Error("Invalid fixture storage");
  return { id: value.id, variant: value.variant, draft };
}

export function readWorkspace(
  defaults: ConsoleRecord[],
): { records: StoredRecord[]; selected: number } | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw === null) {
    const legacy = readDraft();
    return legacy
      ? {
          records: defaults.map((record, index) => ({
            id: record.id,
            variant: record.variant,
            draft:
              index === 0
                ? { ...legacy, disclosure: DEFAULT_DISCLOSURE }
                : record.draft,
          })),
          selected: 0,
        }
      : null;
  }
  if (raw.length > 32768) throw new Error("Invalid fixture storage");
  const value: unknown = JSON.parse(raw);
  if (
    !value ||
    typeof value !== "object" ||
    !("schema" in value) ||
    value.schema !== 2 ||
    !("records" in value) ||
    !Array.isArray(value.records) ||
    value.records.length < 3 ||
    value.records.length > 12 ||
    !("selected" in value) ||
    typeof value.selected !== "number" ||
    !Number.isInteger(value.selected) ||
    value.selected < 0 ||
    value.selected >= value.records.length
  )
    throw new Error("Invalid fixture storage");
  return { records: value.records.map(storedRecord), selected: value.selected };
}

export function writeWorkspace(
  records: ConsoleRecord[],
  selected: number,
): void {
  const safe = records.map((record) => ({
    id: record.id,
    variant: record.variant,
    draft: boundedDraft(record.draft),
  }));
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ schema: 2, selected, records: safe }),
  );
}

export function publicFixture(record: ConsoleRecord) {
  return {
    demo: true,
    signed: false,
    persona: record.committed.name,
    biography: record.committed.bio,
    ai_disclosure: record.committed.disclosure,
    version: `fixture-v${record.revision}`,
    review: record.reviewed ? "demo_reviewed" : "pending",
    campaign: record.approved ? "A quieter kind of summer" : null,
  };
}

export function downloadPublicFixture(record: ConsoleRecord): void {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(publicFixture(record), null, 2)], {
      type: "application/json",
    }),
  );
  try {
    const link = document.createElement("a");
    link.href = url;
    link.download = `${record.id}-fictional-passport-unsigned.json`;
    link.click();
  } finally {
    URL.revokeObjectURL(url);
  }
}
