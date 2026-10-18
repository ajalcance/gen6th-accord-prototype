/** Transient studio query receipts. Cosine values are not identity probabilities. */
import type { PersonaVersion } from "./persona-contracts";
import {
  finite,
  parseBox,
  parseInfo,
  type FaceBox,
  type RepresentationInfo,
} from "./persona-faces";
import { parseVersion } from "./persona-receipts";
import {
  choice,
  hex,
  integer,
  list,
  object,
  requireContract,
  text,
  timestamp,
  uuid,
} from "./persona-validation";

export type QueryReceipt = {
  workspace_id: string;
  query_id: string;
  source_sha256: string;
  analysis_sha256: string;
  thumbnail_sha256: string;
  width: number;
  height: number;
  detector: string;
  decoder_version: string;
  capture_recipe: "rgba-png-1024-v1";
  issued_at: string;
  expires_at: string;
  faces: FaceBox[];
  state: "no_face" | "selection_required";
};
export type SearchCommand = {
  query_id: string;
  request_id: string;
  face_index: number;
  scope: "current" | "history";
};
export type SimilarityCandidate = {
  version: PersonaVersion;
  portrait_id: string;
  generation_id: string;
  face: FaceBox;
  face_cosine: number;
  whole_cosine: number;
  compatible_references: number;
};
export type SimilarityPage = SearchCommand & {
  workspace_id: string;
  method: "exact-cosine-face-max-v1";
  policy_id: string;
  evidence_sha256: string;
  representation: RepresentationInfo | null;
  state:
    | "candidate_review"
    | "no_confident_match"
    | "empty_catalogue"
    | "no_compatible_references"
    | "quality_blocked";
  reasons: string[];
  reference_count: number;
  compatible_count: number;
  items: SimilarityCandidate[];
  has_more: boolean;
};
export type SimilarityReadiness = {
  workspace_id: string;
  state:
    | "processing_unavailable"
    | "calibration_required"
    | "calibration_expired"
    | "ready";
  policy_id: string | null;
};

export function parseQueryReceipt(value: unknown): QueryReceipt {
  const r = object(value, [
    "workspace_id",
    "query_id",
    "source_sha256",
    "analysis_sha256",
    "thumbnail_sha256",
    "width",
    "height",
    "detector",
    "decoder_version",
    "capture_recipe",
    "issued_at",
    "expires_at",
    "faces",
    "state",
  ]);
  return parseQueryFields(r);
}

function parseQueryFields(r: Record<string, unknown>): QueryReceipt {
  const width = integer(r.width),
    height = integer(r.height),
    faces = list(r.faces, parseBox, 10);
  const issued_at = timestamp(r.issued_at),
    expires_at = timestamp(r.expires_at);
  const lifetime = Date.parse(expires_at) - Date.parse(issued_at);
  const state = choice(r.state, ["no_face", "selection_required"]);
  requireContract(
    width <= 1024 &&
      height <= 1024 &&
      lifetime > 0 &&
      lifetime <= 600000 &&
      r.capture_recipe === "rgba-png-1024-v1",
  );
  requireContract(
    Boolean(faces.length) === (state === "selection_required") &&
      faces.every(
        (f, i) =>
          f.index === i && f.x + f.width <= width && f.y + f.height <= height,
      ),
  );
  return {
    workspace_id: uuid(r.workspace_id),
    query_id: uuid(r.query_id),
    source_sha256: hex(r.source_sha256, 64),
    analysis_sha256: hex(r.analysis_sha256, 64),
    thumbnail_sha256: hex(r.thumbnail_sha256, 64),
    width,
    height,
    detector: text(r.detector, 160),
    decoder_version: text(r.decoder_version, 40),
    capture_recipe: r.capture_recipe,
    issued_at,
    expires_at,
    faces,
    state,
  };
}

export function parseCandidate(value: unknown): SimilarityCandidate {
  const r = object(value, [
    "version",
    "portrait_id",
    "generation_id",
    "face",
    "face_cosine",
    "whole_cosine",
    "compatible_references",
  ]);
  const compatible_references = integer(r.compatible_references);
  const face = parseBox(r.face);
  requireContract(compatible_references <= 128);
  requireContract(
    face.index <= 9 &&
      face.x <= 1023 &&
      face.y <= 1023 &&
      face.width <= 1024 &&
      face.height <= 1024,
  );
  return {
    version: parseVersion(r.version),
    portrait_id: uuid(r.portrait_id),
    generation_id: uuid(r.generation_id),
    face,
    face_cosine: finite(r.face_cosine, -1, 1),
    whole_cosine: finite(r.whole_cosine, -1, 1),
    compatible_references,
  };
}

export function parseSimilarityPage(value: unknown): SimilarityPage {
  const r = object(value, [
    "query_id",
    "request_id",
    "face_index",
    "scope",
    "workspace_id",
    "method",
    "policy_id",
    "evidence_sha256",
    "representation",
    "state",
    "reasons",
    "reference_count",
    "compatible_count",
    "items",
    "has_more",
  ]);
  return parsePageFields(r);
}

function parsePageFields(r: Record<string, unknown>): SimilarityPage {
  const items = list(r.items, parseCandidate, 5),
    workspace_id = uuid(r.workspace_id);
  const state = choice(r.state, [
    "candidate_review",
    "no_confident_match",
    "empty_catalogue",
    "no_compatible_references",
    "quality_blocked",
  ]);
  const reference_count = integer(r.reference_count, 0),
    compatible_count = integer(r.compatible_count, 0);
  const face_index = integer(r.face_index, 0);
  requireContract(
    r.method === "exact-cosine-face-max-v1" && typeof r.has_more === "boolean",
  );
  const page: SimilarityPage = {
    query_id: uuid(r.query_id),
    request_id: uuid(r.request_id),
    face_index,
    scope: choice(r.scope, ["current", "history"]),
    workspace_id,
    method: r.method,
    policy_id: text(r.policy_id, 160),
    evidence_sha256: hex(r.evidence_sha256, 64),
    representation:
      r.representation === null ? null : parseInfo(r.representation),
    state,
    reasons: list(
      r.reasons,
      (v) =>
        choice(v, [
          "small_face",
          "low_detection_confidence",
          "extreme_pose",
          "blur",
        ]),
      4,
    ),
    reference_count,
    compatible_count,
    items,
    has_more: r.has_more,
  };
  validatePage(page);
  return page;
}

function validatePage(p: SimilarityPage) {
  requireContract(
    p.state === "quality_blocked"
      ? !p.representation &&
          p.reasons.length > 0 &&
          p.reference_count === 0 &&
          p.compatible_count === 0
      : !!p.representation && p.reasons.length === 0,
  );
  requireContract(p.state !== "empty_catalogue" || p.reference_count === 0);
  requireContract(
    p.state !== "no_compatible_references" ||
      (p.reference_count > 0 && p.compatible_count === 0),
  );
  requireContract(
    !["candidate_review", "no_confident_match"].includes(p.state) ||
      p.compatible_count > 0,
  );
  requireContract(p.face_index <= 9 && (!p.has_more || p.items.length === 5));
  requireContract(
    p.reference_count <= 128 &&
      p.compatible_count <= p.reference_count &&
      Boolean(p.items.length) === (p.state === "candidate_review"),
  );
  requireContract(
    new Set(p.items.map((c) => c.version.persona_id)).size === p.items.length &&
      p.items.every(
        (c, i) =>
          c.version.workspace_id === p.workspace_id &&
          (i === 0 || p.items[i - 1].face_cosine >= c.face_cosine),
      ),
  );
}
