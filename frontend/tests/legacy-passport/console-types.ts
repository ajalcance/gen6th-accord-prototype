import type { Draft } from "./fixture-data";

export type AnalysisStatus =
  "idle" | "running" | "ready" | "error" | "cancelled";
export type DrawerKind =
  "assistant" | "records" | "operations" | "commands" | "governance" | null;
export type FixtureWindow = "before" | "active" | "expired";
export type HistoryEntry = {
  id: number;
  title: string;
  detail: string;
  revision: number;
};
export type ScopeDraft = {
  purpose: string;
  conditions: string;
  startsAt: string;
  endsAt: string;
};
export type ConsoleRecord = {
  id: string;
  variant: number;
  draft: Draft;
  committed: Draft;
  revision: number;
  analysis: AnalysisStatus;
  phase: number;
  candidate: boolean;
  comparison: number;
  comment: string;
  reviewed: boolean;
  confirmed: boolean;
  approved: boolean;
  offered: boolean;
  withdrawn: boolean;
  revoked: boolean;
  scope: ScopeDraft;
  campaignActor: "creator" | "recipient";
  reviewActor: "creator" | "reviewer";
  window: FixtureWindow;
  history: HistoryEntry[];
};
export type ConsoleState = {
  records: ConsoleRecord[];
  selected: number;
  step: number;
  filter: string;
  search: string;
  publicView: boolean;
  drawer: DrawerKind;
  assistantQuestion: string;
  sidebarCollapsed: boolean;
};
export type ConsoleAction =
  | { type: "new" }
  | { type: "select"; index: number }
  | {
      type: "restore";
      records: Pick<ConsoleRecord, "id" | "variant" | "draft">[];
      selected: number;
    }
  | { type: "edit"; key: keyof Draft; value: string }
  | { type: "step"; step: number }
  | { type: "sidebar"; value: boolean }
  | { type: "commit" }
  | { type: "analysis"; status: AnalysisStatus }
  | { type: "phase"; index: number; recordId: string }
  | { type: "note"; value: string }
  | { type: "candidate"; value: boolean }
  | { type: "comparison"; value: number }
  | { type: "review" }
  | { type: "reviewChanges" }
  | { type: "confirm"; value: boolean }
  | { type: "offer" }
  | { type: "accept" }
  | { type: "campaignChanges" }
  | { type: "revoke" }
  | { type: "scope"; key: keyof ScopeDraft; value: string }
  | { type: "campaignActor"; actor: ConsoleRecord["campaignActor"] }
  | { type: "reviewActor"; actor: ConsoleRecord["reviewActor"] }
  | { type: "window"; value: FixtureWindow }
  | { type: "filter"; value: string }
  | { type: "search"; value: string }
  | { type: "publicView"; value: boolean }
  | { type: "drawer"; value: DrawerKind }
  | { type: "question"; value: string };
