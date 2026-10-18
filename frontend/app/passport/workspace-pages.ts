export const workspacePages = [
  "Records",
  "System Capture",
  "Analysis & review",
  "Production & use",
  "Passports",
  "Settings",
] as const;

export type WorkspacePage = (typeof workspacePages)[number];
export type JourneyPage =
  "Analysis & review" | "Production & use" | "Passports";
export const journeyEntries: Record<
  JourneyPage,
  { description: string; action: string }
> = {
  "Analysis & review": {
    description:
      "Compare appearances with approved references, inspect findings and request independent review.",
    action: "Open analysis",
  },
  "Production & use": {
    description:
      "Manage production offers, current permissions and recipient decisions for a saved performer.",
    action: "Manage production use",
  },
  Passports: {
    description:
      "Issue private passports, manage public sharing and verify passport packages.",
    action: "Open passports",
  },
};
export type RecordSection =
  | "Overview"
  | "References"
  | "Evidence & assets"
  | "Rights & operator"
  | "Activity";
export type RecordTarget = {
  id: string;
  revision: number | null;
  section: RecordSection;
};
export type RecordNavigation = {
  open: (id: string, section?: RecordSection) => void;
  navigate: (page: WorkspacePage) => void;
  version: (revision: number | null) => void;
  loaded?: (id: string, revision: number) => void;
};
