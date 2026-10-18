/** Capture provenance and approved references; no analysis bytes or model verdicts enter the browser. */
import { apiClient } from "./api-client";
import { fetchPrivatePng } from "./persona-photos";
import {
  hex,
  integer,
  list,
  object,
  requireContract,
  text,
  timestamp,
  uuid,
} from "./persona-validation";

export type CaptureMetadata = {
  portrait_id: string;
  source_sha256: string;
  source_width: number;
  source_height: number;
  orientation: number;
  width: number;
  height: number;
  sha256: string;
  recipe: "rgba-png-1024-v1";
  decoder_version: string;
  recorded_at: string;
};
export type CaptureQuery = {
  upload_id: string | null;
  version_id: string | null;
};
export type CaptureProfile = CaptureQuery & {
  workspace_id: string;
  portrait_id: string | null;
  capture: CaptureMetadata | null;
  references: CaptureMetadata[];
  recognition: "not_processed";
};
export type CaptureGateway = {
  workspaceId: string;
  query: (
    command: CaptureQuery,
    signal: AbortSignal,
  ) => Promise<CaptureProfile>;
  thumbnail: (
    version: string,
    portrait: string,
    signal: AbortSignal,
  ) => Promise<Blob>;
};

export function parseCapture(value: unknown): CaptureMetadata {
  const row = object(value, [
    "portrait_id",
    "source_sha256",
    "source_width",
    "source_height",
    "orientation",
    "width",
    "height",
    "sha256",
    "recipe",
    "decoder_version",
    "recorded_at",
  ]);
  const sw = integer(row.source_width),
    sh = integer(row.source_height),
    orientation = integer(row.orientation);
  const width = integer(row.width),
    height = integer(row.height);
  requireContract(
    sw <= 4096 &&
      sh <= 4096 &&
      sw * sh <= 8000000 &&
      orientation <= 8 &&
      width <= 1024 &&
      height <= 1024 &&
      width <= (orientation >= 5 ? sh : sw) &&
      height <= (orientation >= 5 ? sw : sh) &&
      row.recipe === "rgba-png-1024-v1",
  );
  return {
    portrait_id: uuid(row.portrait_id),
    source_sha256: hex(row.source_sha256, 64),
    source_width: sw,
    source_height: sh,
    orientation,
    width,
    height,
    sha256: hex(row.sha256, 64),
    recipe: row.recipe,
    decoder_version: text(row.decoder_version, 40),
    recorded_at: timestamp(row.recorded_at),
  };
}

export function parseCaptureProfile(value: unknown): CaptureProfile {
  const row = object(value, [
    "workspace_id",
    "upload_id",
    "version_id",
    "portrait_id",
    "capture",
    "references",
    "recognition",
  ]);
  const upload_id = row.upload_id === null ? null : uuid(row.upload_id);
  const version_id = row.version_id === null ? null : uuid(row.version_id);
  const portrait_id = row.portrait_id === null ? null : uuid(row.portrait_id);
  const capture = row.capture === null ? null : parseCapture(row.capture);
  const references = list(row.references, parseCapture, 8);
  requireContract(
    (upload_id === null) !== (version_id === null) &&
      row.recognition === "not_processed" &&
      (!capture || capture.portrait_id === portrait_id) &&
      (!upload_id || (portrait_id === upload_id && !references.length)) &&
      new Set(references.map((item) => item.portrait_id)).size ===
        references.length,
  );
  return {
    workspace_id: uuid(row.workspace_id),
    upload_id,
    version_id,
    portrait_id,
    capture,
    references,
    recognition: row.recognition,
  };
}

export function captureGateway(workspace: string): CaptureGateway {
  const workspaceId = uuid(workspace),
    path = `/api/workspaces/${workspaceId}/personas/photos`;
  return {
    workspaceId,
    async query(command, signal) {
      const page = parseCaptureProfile(
        await apiClient.post<unknown>(`${path}/capture/query`, command, {
          signal,
          credentials: "same-origin",
          mode: "same-origin",
          cache: "no-store",
          redirect: "error",
          retries: 0,
        }),
      );
      requireContract(
        !signal.aborted &&
          page.workspace_id === workspaceId &&
          page.upload_id === command.upload_id &&
          page.version_id === command.version_id,
      );
      return page;
    },
    async thumbnail(version, portrait, signal) {
      const blob = await fetchPrivatePng(
        `${path}/versions/${uuid(version)}/references/${uuid(portrait)}/thumbnail`,
        signal,
      );
      requireContract(blob !== null);
      return blob;
    },
  };
}
