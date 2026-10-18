"use client";
import { createContext, useContext } from "react";
import type { PersonaGateway } from "../../lib/persona-gateway";
import type { CampaignReceipt } from "../../lib/persona-contracts";
import type { PhotoGateway } from "../../lib/persona-photos";
import type { PortraitSearchGateway } from "../../lib/persona-portrait-search";
import type { CaptureGateway } from "../../lib/persona-captures";
import type { FaceGateway } from "../../lib/persona-faces";
import type { SimilarityGateway } from "../../lib/persona-similarity";
import type { InvestigationGateway } from "../../lib/persona-investigations";
import type { PassportGateway } from "../../lib/persona-passports";
import type { RuntimeGateway } from "../../lib/persona-runtime";
import type { EvidenceGateway } from "../../lib/persona-evidence";
import type { AssetRegistry } from "../../lib/persona-assets";
import type { PublicationGateway } from "../../lib/persona-publications";
import type { CreditGateway } from "../../lib/persona-credits";
import type { LifecycleGateway } from "../../lib/persona-lifecycle";
import type { AssistantGateway } from "../../lib/persona-assistant";

/** Set only after verified same-origin session discovery. The server authorizes every request. */
export type SavedPersonaSource = {
  workspaceId: string;
  workspaceLabel: string;
  sessionKey: string;
  gateway: PersonaGateway;
  /** Explicit existing-record actions, using the same verified workspace session. */
  writeGateway?: PersonaGateway;
  photos?: PhotoGateway;
  portraitSearch?: PortraitSearchGateway;
  captures?: CaptureGateway;
  faces?: FaceGateway;
  similarity?: SimilarityGateway;
  investigations?: InvestigationGateway;
  passports?: PassportGateway;
  runtime?: RuntimeGateway;
  evidence?: EvidenceGateway;
  assetRegistry?: AssetRegistry;
  publications?: PublicationGateway;
  credits?: CreditGateway;
  lifecycle?: LifecycleGateway;
  /** Optional advisory reviewer brief; the server answers 503 until the capability is enabled. */
  assistant?: AssistantGateway;
  assets?: { version_id: string; assets: CampaignReceipt["assets"] }[];
};
export const SavedSourceContext = createContext<SavedPersonaSource | null>(
  null,
);
export const useSavedSource = () => useContext(SavedSourceContext);
