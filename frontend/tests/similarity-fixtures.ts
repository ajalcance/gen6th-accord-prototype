/** Synthetic query and vector receipts; no real similarity accuracy evidence. */
import type {
  QueryReceipt,
  SearchCommand,
  SimilarityPage,
} from "../lib/persona-similarity-contracts";
import { detected } from "./face-fixtures";
import { version } from "./prepared-write-fixtures";

export function queryReceipt(): QueryReceipt {
  return {
    workspace_id: version.workspace_id,
    query_id: detected.request_id,
    source_sha256: "a".repeat(64),
    analysis_sha256: "b".repeat(64),
    thumbnail_sha256: "c".repeat(64),
    width: detected.width,
    height: detected.height,
    detector: "synthetic-detector",
    decoder_version: "synthetic-decoder",
    capture_recipe: "rgba-png-1024-v1",
    issued_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 600000).toISOString(),
    faces: detected.faces,
    state: "selection_required",
  };
}
export const command: SearchCommand = {
  query_id: detected.request_id,
  request_id: detected.generation_id,
  face_index: 1,
  scope: "current",
};
export function similarityPage(intent = command): SimilarityPage {
  return {
    ...intent,
    workspace_id: version.workspace_id,
    method: "exact-cosine-face-max-v1",
    policy_id: "synthetic-reviewed-policy",
    evidence_sha256: "d".repeat(64),
    representation: {
      model: "synthetic-model",
      provider_revision: "fixture-v1",
      dimensions: 2,
      crop_recipe: "face-square-512-v1",
      crop_sha256: "e".repeat(64),
      quality_policy: "provisional-face-v1",
      calibration: "benchmark_pending",
    },
    state: "candidate_review",
    reasons: [],
    reference_count: 2,
    compatible_count: 1,
    items: [
      {
        version,
        portrait_id: detected.portrait_id,
        generation_id: detected.generation_id,
        face: detected.faces[0],
        face_cosine: 0.95,
        whole_cosine: -0.3,
        compatible_references: 1,
      },
    ],
    has_more: false,
  };
}

export function queryImage(): File {
  const file = new File(["fixture"], "query.png", { type: "image/png" });
  Object.defineProperty(file, "arrayBuffer", {
    value: async () => new TextEncoder().encode("fixture").buffer,
  });
  return file;
}
