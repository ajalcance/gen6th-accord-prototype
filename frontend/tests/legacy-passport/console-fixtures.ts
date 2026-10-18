import type { ConsoleRecord, ConsoleState, ScopeDraft } from "./console-types";
import { isDraftReady } from "./fixture-data";

export const SCAN_PHASES = [
  "Prepare artifact",
  "Inspect composition",
  "Compare references",
  "Organize evidence",
  "Ready for human review",
];
export const SCAN_DURATION_MS = 3600;
export const FIXTURES = [
  {
    id: "nova",
    name: "Nova Vale",
    category: "Editorial · lifestyle",
    bio: "A fictional editorial persona exploring design, travel and slower living.",
    contribution:
      "Art direction, character concept and original vector illustration.",
  },
  {
    id: "iris",
    name: "Iris Sol",
    category: "Culture · creative",
    bio: "A fictional cultural correspondent collecting stories about art and community.",
    contribution:
      "Character writing, creative direction and original vector color study.",
  },
  {
    id: "arden",
    name: "Arden Grey",
    category: "Design · future",
    bio: "A fictional design researcher investigating materials and future cities.",
    contribution:
      "Worldbuilding, design research and original vector color study.",
  },
];

export function initialRecord(index: number): ConsoleRecord {
  const fixture = FIXTURES[index];
  const draft = {
    name: fixture.name,
    bio: fixture.bio,
    contribution: fixture.contribution,
    disclosure:
      "Fictional synthetic character concept. Original vector study; no real person or generation log.",
  };
  return {
    id: fixture.id,
    variant: index,
    draft,
    committed: { ...draft },
    revision: 1,
    analysis: "idle",
    phase: 0,
    candidate: false,
    comparison: 50,
    comment: "",
    reviewed: false,
    confirmed: false,
    approved: false,
    offered: false,
    withdrawn: false,
    revoked: false,
    campaignActor: "creator",
    reviewActor: "reviewer",
    window: "before",
    scope: {
      purpose: "Editorial campaign concept",
      conditions:
        "AI disclosure required. No resale, voice cloning or sublicensing.",
      startsAt: "2026-10-15",
      endsAt: "2026-11-15",
    },
    history: [
      {
        id: 1,
        title: "Fixture record opened",
        detail: "Browser-only illustration study; no server receipt.",
        revision: 1,
      },
    ],
  };
}

export function newRecord(index: number): ConsoleRecord {
  const record = initialRecord(index % 3);
  const draft = {
    name: "",
    bio: "",
    contribution: "",
    disclosure:
      "Fictional synthetic character. Complete the evidence disclosure.",
  };
  return {
    ...record,
    id: `local-${index + 1}`,
    draft,
    committed: { ...draft },
    history: [
      {
        id: 1,
        title: "New fictional draft",
        detail: "Complete the System Capture fields; no server record exists.",
        revision: 1,
      },
    ],
  };
}

export function initialConsole(): ConsoleState {
  return {
    records: FIXTURES.map((_, index) => initialRecord(index)),
    selected: 0,
    step: 0,
    filter: "All personas",
    search: "",
    publicView: true,
    drawer: null,
    assistantQuestion: "evidence",
    sidebarCollapsed: false,
  };
}

export function isDirty(record: ConsoleRecord): boolean {
  return JSON.stringify(record.draft) !== JSON.stringify(record.committed);
}

export function scopeIsValid(scope: ScopeDraft): boolean {
  const validDate = (value: string) =>
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    new Date(`${value}T00:00:00Z`).toISOString().slice(0, 10) === value;
  try {
    if (!validDate(scope.startsAt) || !validDate(scope.endsAt)) return false;
    const days =
      (Date.parse(scope.endsAt) - Date.parse(scope.startsAt)) / 86400000;
    return (
      days > 0 &&
      days <= 366 &&
      [scope.purpose, scope.conditions].every(
        (value) => value.trim().length > 0 && value.length <= 500,
      )
    );
  } catch {
    return false;
  }
}

export function campaignBlocks(record: ConsoleRecord): string[] {
  const blocks: string[] = [];
  if (!record.reviewed || isDirty(record))
    blocks.push("The current version needs an independent review.");
  if (!record.offered || !record.approved)
    blocks.push("The named recipient has not accepted a current offer.");
  if (record.withdrawn)
    blocks.push("The recipient requested changes; a new offer is required.");
  if (record.revoked)
    blocks.push("The creator revoked this offer; it cannot be reopened.");
  if (record.window === "before")
    blocks.push("The campaign window has not started.");
  if (record.window === "expired")
    blocks.push("The campaign window has expired.");
  return blocks;
}

export function canAccept(record: ConsoleRecord): boolean {
  return (
    record.reviewed &&
    scopeIsValid(record.scope) &&
    isDraftReady(record.draft) &&
    !isDirty(record) &&
    record.offered &&
    record.confirmed &&
    !record.revoked &&
    !record.withdrawn &&
    !record.approved &&
    record.campaignActor === "recipient" &&
    record.window !== "expired"
  );
}
