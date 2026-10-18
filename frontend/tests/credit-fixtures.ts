import type {
  CreditContent,
  CreditConfirmation,
  CreditProfile,
  CreditSnapshot,
} from "../lib/persona-credits";
import { version } from "./prepared-write-fixtures";

export const creditContent: CreditContent = {
  aliases: ["Nova"],
  credits: [
    {
      name: "Ari",
      kind: "human",
      role: "design",
      actor_ref: "contributor-a",
      evidence_id: null,
    },
  ],
};
export const creditSnapshot: CreditSnapshot = {
  id: "00000000-0000-4000-8000-000000000101",
  workspace_id: version.workspace_id,
  version_id: version.version_id,
  request_id: "00000000-0000-4000-8000-000000000102",
  ordinal: 1,
  declared_by: version.creator_ref,
  recorded_at: version.recorded_at,
  content: creditContent,
};
export const creditConfirmation: CreditConfirmation = {
  id: "00000000-0000-4000-8000-000000000103",
  workspace_id: version.workspace_id,
  version_id: version.version_id,
  request_id: "00000000-0000-4000-8000-000000000104",
  profile_id: creditSnapshot.id,
  credit_index: 0,
  actor_ref: "contributor-a",
  recorded_at: version.recorded_at,
};
export const creditProfile: CreditProfile = {
  workspace_id: version.workspace_id,
  version_id: version.version_id,
  snapshot: creditSnapshot,
  confirmations: [],
};
