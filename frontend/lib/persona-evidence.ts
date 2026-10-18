/** Private bytes stay in memory. Every mutation is manual and uses the same-origin session. */
import { ApiError, apiClient } from "./api-client";
import { parseEvidenceStatus } from "./persona-evidence-receipts";
import type { EvidenceStatus } from "./persona-read-contracts";
import { requireContract, uuid } from "./persona-validation";

export type EvidenceUpload = {
  requestId: string;
  versionId: string;
  digest: string;
  file: File;
};
export type EvidenceGateway = {
  workspaceId: string;
  readiness(signal: AbortSignal): Promise<{
    upload_available: boolean;
    inspection_available: boolean;
    download_available: boolean;
    purge_available: boolean;
  }>;
  purge(id: string, signal: AbortSignal): Promise<EvidenceStatus>;
  upload(command: EvidenceUpload, signal: AbortSignal): Promise<EvidenceStatus>;
  inspect(id: string, signal: AbortSignal): Promise<EvidenceStatus>;
  download(row: EvidenceStatus, signal: AbortSignal): Promise<Blob>;
};

export async function prepareEvidence(
  file: File,
  versionId: string,
): Promise<EvidenceUpload> {
  requireContract(
    ["image/png", "image/jpeg", "text/plain"].includes(file.type),
  );
  requireContract(file.size > 0 && file.size <= 10485760);
  const digest = await crypto.subtle.digest(
    "SHA-256",
    await file.arrayBuffer(),
  );
  return {
    requestId: crypto.randomUUID(),
    versionId: uuid(versionId),
    file,
    digest: Array.from(new Uint8Array(digest), (value) =>
      value.toString(16).padStart(2, "0"),
    ).join(""),
  };
}

export function evidenceGateway(workspace: string): EvidenceGateway {
  const workspaceId = uuid(workspace),
    path = `/api/workspaces/${workspaceId}/personas/evidence`;
  const options = {
    credentials: "same-origin",
    mode: "same-origin",
    cache: "no-store",
    redirect: "error",
    retries: 0,
    timeoutMs: 90000,
  } as const;
  const validate = (raw: unknown, signal: AbortSignal) => {
    const row = parseEvidenceStatus(raw);
    requireContract(!signal.aborted && row.workspace_id === workspaceId);
    return row;
  };
  return {
    workspaceId,
    async readiness(signal) {
      const raw = await apiClient.post(
        path + "/readiness",
        {},
        { ...options, signal },
      );
      requireContract(raw !== null && typeof raw === "object");
      const row = raw as Record<string, unknown>;
      requireContract(
        Object.keys(row).sort().join() ===
          "download_available,inspection_available,purge_available,upload_available,workspace_id" &&
          row.workspace_id === workspaceId &&
          !signal.aborted,
      );
      const keys = [
        "upload_available",
        "inspection_available",
        "download_available",
        "purge_available",
      ] as const;
      for (const key of keys) requireContract(typeof row[key] === "boolean");
      return {
        upload_available: row.upload_available as boolean,
        inspection_available: row.inspection_available as boolean,
        download_available: row.download_available as boolean,
        purge_available: row.purge_available as boolean,
      };
    },
    async purge(id, signal) {
      const row = validate(
        await apiClient.post(
          path + "/purge",
          { evidence_id: uuid(id) },
          { ...options, signal },
        ),
        signal,
      );
      requireContract(row.id === id && row.state === "expired");
      return row;
    },
    async upload(command, signal) {
      const response = await fetch(
        `${path}/upload/${uuid(command.versionId)}`,
        {
          ...options,
          method: "POST",
          signal: AbortSignal.any([signal, AbortSignal.timeout(45000)]),
          body: command.file,
          headers: {
            "Content-Type": command.file.type,
            "X-Request-ID": uuid(command.requestId),
            "X-Content-SHA256": command.digest,
            "X-Evidence-Length": String(command.file.size),
          },
        },
      );
      if (!response.ok)
        throw new ApiError("Evidence upload unavailable", response.status);
      const row = validate(await response.json(), signal);
      requireContract(
        row.version_id === command.versionId &&
          row.sha256 === command.digest &&
          row.byte_length === command.file.size &&
          row.media_type === command.file.type,
      );
      return row;
    },
    async inspect(id, signal) {
      const row = validate(
        await apiClient.post(
          path + "/inspect",
          { evidence_id: uuid(id) },
          { ...options, signal },
        ),
        signal,
      );
      requireContract(row.id === id);
      return row;
    },
    async download(row, signal) {
      requireContract(
        row.workspace_id === workspaceId && row.state === "clean",
      );
      const response = await fetch(path + "/content", {
        ...options,
        method: "POST",
        signal: AbortSignal.any([signal, AbortSignal.timeout(30000)]),
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ evidence_id: uuid(row.id) }),
      });
      if (!response.ok)
        throw new ApiError("Evidence download unavailable", response.status);
      requireContract(
        response.headers.get("content-type") === "application/octet-stream" &&
          response.headers.get("x-content-sha256") === row.sha256 &&
          response.body !== null,
      );
      const reader = response.body.getReader(),
        chunks: Uint8Array<ArrayBuffer>[] = [];
      let total = 0;
      try {
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          total += value.length;
          requireContract(total <= row.byte_length && total <= 10485760);
          chunks.push(new Uint8Array(value));
        }
      } finally {
        await reader.cancel();
      }
      requireContract(total === row.byte_length && !signal.aborted);
      const blob = new Blob(chunks, { type: "application/octet-stream" });
      const digest = new Uint8Array(
        await crypto.subtle.digest("SHA-256", await blob.arrayBuffer()),
      );
      requireContract(
        Array.from(digest, (v) => v.toString(16).padStart(2, "0")).join("") ===
          row.sha256 && !signal.aborted,
      );
      return blob;
    },
  };
}
