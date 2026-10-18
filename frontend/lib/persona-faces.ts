/** Private version/reference face receipts; vectors and image bytes are never response fields. */
import { apiClient } from "./api-client";
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

export type FaceBox = {
  index: number;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number;
  yaw: number;
  pitch: number;
  blur: string;
};
export type FaceSubject = { version_id: string; portrait_id: string };
export type FaceCommand = FaceSubject & {
  request_id: string;
  generation_id: string | null;
  face_index: number | null;
};
export type RepresentationInfo = {
  model: string;
  provider_revision: string;
  dimensions: number;
  crop_recipe: string;
  crop_sha256: string;
  quality_policy: string;
  calibration: "benchmark_pending";
};
export type FaceResult = FaceSubject & {
  workspace_id: string;
  request_id: string;
  generation_id: string;
  parent_id: string | null;
  source_sha256: string;
  width: number;
  height: number;
  detector: string;
  recorded_at: string;
  faces: FaceBox[];
  selected: number | null;
  state: "no_face" | "selection_required" | "quality_blocked" | "represented";
  reasons: string[];
  representation: RepresentationInfo | null;
};
export type FaceProfile = FaceSubject & {
  workspace_id: string;
  latest: FaceResult | null;
  provider_ready: boolean;
};
export type FaceGateway = {
  workspaceId: string;
  query: (subject: FaceSubject, signal: AbortSignal) => Promise<FaceProfile>;
  process: (command: FaceCommand, signal: AbortSignal) => Promise<FaceResult>;
};

export function finite(value: unknown, min: number, max: number): number {
  requireContract(
    typeof value === "number" &&
      Number.isFinite(value) &&
      value >= min &&
      value <= max,
  );
  return value;
}
export function parseBox(value: unknown): FaceBox {
  const row = object(value, [
    "index",
    "x",
    "y",
    "width",
    "height",
    "confidence",
    "yaw",
    "pitch",
    "blur",
  ]);
  return {
    index: integer(row.index, 0),
    x: integer(row.x, 0),
    y: integer(row.y, 0),
    width: integer(row.width),
    height: integer(row.height),
    confidence: finite(row.confidence, 0, 1),
    yaw: finite(row.yaw, -180, 180),
    pitch: finite(row.pitch, -180, 180),
    blur: choice(row.blur, [
      "UNKNOWN",
      "VERY_UNLIKELY",
      "UNLIKELY",
      "POSSIBLE",
      "LIKELY",
      "VERY_LIKELY",
    ]),
  };
}
export function parseInfo(value: unknown): RepresentationInfo {
  const row = object(value, [
    "model",
    "provider_revision",
    "dimensions",
    "crop_recipe",
    "crop_sha256",
    "quality_policy",
    "calibration",
  ]);
  const dimensions = integer(row.dimensions);
  requireContract(
    dimensions <= 1408 &&
      row.crop_recipe === "face-square-512-v1" &&
      row.quality_policy === "provisional-face-v1" &&
      row.calibration === "benchmark_pending",
  );
  return {
    model: text(row.model, 160),
    provider_revision: text(row.provider_revision, 160),
    dimensions,
    crop_recipe: row.crop_recipe,
    crop_sha256: hex(row.crop_sha256, 64),
    quality_policy: row.quality_policy,
    calibration: row.calibration,
  };
}
export function parseFaceResult(value: unknown): FaceResult {
  const r = object(value, [
    "workspace_id",
    "version_id",
    "portrait_id",
    "request_id",
    "generation_id",
    "parent_id",
    "source_sha256",
    "width",
    "height",
    "detector",
    "recorded_at",
    "faces",
    "selected",
    "state",
    "reasons",
    "representation",
  ]);
  return parseFaceFields(r);
}
function parseFaceFields(r: Record<string, unknown>): FaceResult {
  const width = integer(r.width),
    height = integer(r.height),
    faces = list(r.faces, parseBox, 10);
  const state = choice(r.state, [
    "no_face",
    "selection_required",
    "quality_blocked",
    "represented",
  ]);
  const selected = r.selected === null ? null : integer(r.selected, 0);
  const parent_id = r.parent_id === null ? null : uuid(r.parent_id);
  const reasons = list(
    r.reasons,
    (v) =>
      choice(v, [
        "small_face",
        "low_detection_confidence",
        "extreme_pose",
        "blur",
      ]),
    4,
  );
  const representation =
    r.representation === null ? null : parseInfo(r.representation);
  const result: FaceResult = {
    workspace_id: uuid(r.workspace_id),
    version_id: uuid(r.version_id),
    portrait_id: uuid(r.portrait_id),
    request_id: uuid(r.request_id),
    generation_id: uuid(r.generation_id),
    parent_id,
    source_sha256: hex(r.source_sha256, 64),
    width,
    height,
    detector: text(r.detector, 160),
    recorded_at: timestamp(r.recorded_at),
    faces,
    selected,
    state,
    reasons,
    representation,
  };
  validateFaceState(result);
  return result;
}
function validateFaceState(r: FaceResult) {
  requireContract(
    r.width <= 1024 &&
      r.height <= 1024 &&
      r.faces.every(
        (f, i) =>
          f.index === i &&
          f.x + f.width <= r.width &&
          f.y + f.height <= r.height,
      ),
  );
  const detection = r.state === "no_face" || r.state === "selection_required";
  requireContract(
    detection
      ? r.parent_id === null &&
          r.selected === null &&
          r.reasons.length === 0 &&
          r.representation === null &&
          Boolean(r.faces.length) === (r.state === "selection_required")
      : r.parent_id !== null &&
          r.selected !== null &&
          r.selected < r.faces.length &&
          Boolean(r.representation) === (r.state === "represented") &&
          Boolean(r.reasons.length) === (r.state === "quality_blocked"),
  );
}
function bound(
  result: FaceSubject & { workspace_id: string },
  subject: FaceSubject,
  workspace: string,
  signal: AbortSignal,
) {
  requireContract(
    !signal.aborted &&
      result.workspace_id === workspace &&
      result.version_id === subject.version_id &&
      result.portrait_id === subject.portrait_id,
  );
}
export function faceGateway(workspace: string): FaceGateway {
  const workspaceId = uuid(workspace),
    path = `/api/workspaces/${workspaceId}/personas/photos/faces`;
  const post = (route: string, body: FaceSubject, signal: AbortSignal) =>
    apiClient.post<unknown>(`${path}/${route}`, body, {
      signal,
      credentials: "same-origin",
      mode: "same-origin",
      cache: "no-store",
      redirect: "error",
      retries: 0,
      timeoutMs: route === "process" ? 75000 : 10000,
    });
  return {
    workspaceId,
    async query(subject, signal) {
      const r = object(await post("query", subject, signal), [
        "workspace_id",
        "version_id",
        "portrait_id",
        "latest",
        "provider_ready",
      ]);
      requireContract(typeof r.provider_ready === "boolean");
      const result = {
        workspace_id: uuid(r.workspace_id),
        version_id: uuid(r.version_id),
        portrait_id: uuid(r.portrait_id),
        provider_ready: r.provider_ready,
        latest: r.latest === null ? null : parseFaceResult(r.latest),
      };
      bound(result, subject, workspaceId, signal);
      if (result.latest) bound(result.latest, subject, workspaceId, signal);
      return result;
    },
    async process(command, signal) {
      const result = parseFaceResult(await post("process", command, signal));
      bound(result, command, workspaceId, signal);
      requireContract(
        result.request_id === command.request_id &&
          result.parent_id === command.generation_id &&
          result.selected === command.face_index,
      );
      return result;
    },
  };
}
