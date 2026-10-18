import type { CaptureMetadata, CaptureProfile } from "../lib/persona-captures";
import { version } from "./prepared-write-fixtures";

export const capture: CaptureMetadata = {
  portrait_id: "00000000-0000-4000-8000-000000000090",
  source_sha256: "a".repeat(64),
  source_width: 1600,
  source_height: 800,
  orientation: 1,
  width: 1024,
  height: 512,
  sha256: "b".repeat(64),
  recipe: "rgba-png-1024-v1",
  decoder_version: "12.3.0",
  recorded_at: version.recorded_at,
};
export const second = {
  ...capture,
  portrait_id: "00000000-0000-4000-8000-000000000091",
};
export const profile: CaptureProfile = {
  workspace_id: version.workspace_id,
  upload_id: null,
  version_id: version.version_id,
  portrait_id: capture.portrait_id,
  capture,
  references: [capture, second],
  recognition: "not_processed",
};
