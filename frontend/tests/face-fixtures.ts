import type { FaceResult } from "../lib/persona-faces";
import { capture } from "./capture-fixtures";
import { version } from "./prepared-write-fixtures";

export const detected: FaceResult = {
  workspace_id: version.workspace_id,
  version_id: version.version_id,
  portrait_id: capture.portrait_id,
  request_id: "00000000-0000-4000-8000-000000000095",
  generation_id: "00000000-0000-4000-8000-000000000096",
  parent_id: null,
  source_sha256: capture.sha256,
  width: capture.width,
  height: capture.height,
  detector: "synthetic-fixture",
  recorded_at: version.recorded_at,
  selected: null,
  state: "selection_required",
  reasons: [],
  representation: null,
  faces: [0, 1].map((index) => ({
    index,
    x: 20 + index * 200,
    y: 20,
    width: 100,
    height: 100,
    confidence: 0.95,
    yaw: 0,
    pitch: 0,
    blur: "UNLIKELY",
  })),
};
