import { version } from "./prepared-write-fixtures";

/** Synthetic server response for the advisory reviewer brief. */
export const wireBrief = {
  persona_id: version.persona_id,
  version_id: version.version_id,
  revision: version.revision,
  state: "brief",
  summary: "The creator states that Nova is a fictional editorial character.",
  gaps: ["Which tools produced the visuals is not stated."],
  questions: ["Which tools did you use to make the visuals?"],
  model: "google/global/gemini-3.8-flash",
  model_revision: "gemini-3.8-flash-001",
  generated_at: "2026-10-17T08:00:00Z",
  notice:
    "Advisory draft from an AI model. An independent human reviewer decides.",
};
