/** Private, explicitly retried photo requests. No credentials or persistent image cache. */
import { apiClient, ApiError } from "./api-client";
import {
  hex,
  integer,
  object,
  requireContract,
  uuid,
} from "./persona-validation";

export type PhotoUploadCommand = {
  request_id: string;
  media_type: "image/png" | "image/jpeg";
  byte_length: number;
  sha256: string;
  data: string;
};
export type PhotoUploadReceipt = {
  id: string;
  workspace_id: string;
  request_id: string;
  sha256: string;
  width: number;
  height: number;
};
export type PhotoGateway = {
  workspaceId: string;
  upload(
    command: PhotoUploadCommand,
    signal: AbortSignal,
  ): Promise<PhotoUploadReceipt>;
  thumbnail(versionId: string, signal: AbortSignal): Promise<Blob | null>;
};

export function parsePhotoReceipt(raw: unknown): PhotoUploadReceipt {
  const row = object(raw, [
    "id",
    "workspace_id",
    "request_id",
    "sha256",
    "width",
    "height",
  ]);
  const width = integer(row.width),
    height = integer(row.height);
  requireContract(width <= 320 && height <= 320);
  return {
    id: uuid(row.id),
    workspace_id: uuid(row.workspace_id),
    request_id: uuid(row.request_id),
    sha256: hex(row.sha256, 64),
    width,
    height,
  };
}

export async function preparePhoto(file: File): Promise<PhotoUploadCommand> {
  requireContract(file.type === "image/png" || file.type === "image/jpeg");
  requireContract(file.size > 0 && file.size <= 10485760);
  const bytes = new Uint8Array(await file.arrayBuffer());
  requireContract(bytes.length === file.size);
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  const sha256 = Array.from(digest, (value) =>
    value.toString(16).padStart(2, "0"),
  ).join("");
  let binary = "";
  for (let i = 0; i < bytes.length; i += 16384)
    binary += String.fromCharCode(...bytes.subarray(i, i + 16384));
  return {
    request_id: crypto.randomUUID(),
    media_type: file.type,
    byte_length: bytes.length,
    sha256,
    data: btoa(binary),
  };
}

export function photoGateway(workspace: string): PhotoGateway {
  const workspaceId = uuid(workspace),
    path = `/api/workspaces/${workspaceId}/personas/photos`;
  return {
    workspaceId,
    async upload(command, signal) {
      const receipt = parsePhotoReceipt(
        await apiClient.post<unknown>(path + "/upload", command, {
          signal,
          credentials: "same-origin",
          mode: "same-origin",
          cache: "no-store",
          redirect: "error",
          retries: 0,
          timeoutMs: 90000,
        }),
      );
      requireContract(
        !signal.aborted &&
          receipt.workspace_id === workspaceId &&
          receipt.request_id === command.request_id &&
          receipt.sha256 === command.sha256,
      );
      return receipt;
    },
    thumbnail: (version, signal) =>
      fetchPrivatePng(`${path}/versions/${uuid(version)}/thumbnail`, signal),
  };
}

export async function fetchPrivatePng(url: string, signal: AbortSignal) {
  const controller = new AbortController(),
    abort = () => controller.abort();
  if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
  signal.addEventListener("abort", abort, { once: true });
  const timer = setTimeout(abort, 10000);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      credentials: "same-origin",
      mode: "same-origin",
      cache: "no-store",
      redirect: "error",
    });
    if (!response.ok) throw new ApiError("Photo unavailable", response.status);
    if (response.status === 204) return null;
    requireContract(
      response.headers.get("content-type")?.split(";")[0] === "image/png",
    );
    requireContract(response.body !== null);
    const reader = response.body.getReader(),
      chunks: Uint8Array<ArrayBuffer>[] = [];
    let total = 0;
    try {
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        total += value.length;
        requireContract(total <= 1048576);
        chunks.push(new Uint8Array(value));
      }
    } finally {
      await reader.cancel();
    }
    requireContract(total > 0 && !signal.aborted);
    const blob = new Blob(chunks, { type: "image/png" });
    const signature = new Uint8Array(await blob.slice(0, 8).arrayBuffer());
    requireContract(signature.join() === "137,80,78,71,13,10,26,10");
    return blob;
  } finally {
    clearTimeout(timer);
    signal.removeEventListener("abort", abort);
  }
}
