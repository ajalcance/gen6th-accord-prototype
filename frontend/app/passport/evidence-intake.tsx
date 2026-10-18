import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../lib/api-client";
import {
  prepareEvidence,
  type EvidenceGateway,
  type EvidenceUpload,
} from "../../lib/persona-evidence";
import type { EvidenceStatus } from "../../lib/persona-read-contracts";
import type { AssetRegistry } from "../../lib/persona-assets";
import AssetEnrollment from "./asset-enrollment";
import type { PersonaGateway } from "../../lib/persona-gateway";
import EvidenceLibrary from "./evidence-library";
import EvidenceDownload from "./evidence-download";
import { usePersonaQuery } from "./use-persona-query";
import { GovernanceRead } from "./governance-common";

export default function EvidenceIntake({
  gateway,
  registry,
  records,
  versionId,
  denied,
}: {
  gateway: EvidenceGateway;
  registry?: AssetRegistry;
  records?: PersonaGateway;
  versionId: string;
  denied: () => void;
}) {
  const [intent, setIntent] = useState<EvidenceUpload | null>(null);
  const [row, setRow] = useState<EvidenceStatus | null>(null);
  const [download, setDownload] = useState<Blob | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const operation = useRef<AbortController | null>(null);
  const selection = useRef(0);
  const { state: readiness, query: config } =
    usePersonaQuery<Awaited<ReturnType<EvidenceGateway["readiness"]>>>();
  useEffect(() => {
    void config.run((signal) => gateway.readiness(signal));
    return () => config.stop();
  }, [gateway, config]);
  useEffect(() => {
    if (readiness.phase === "denied") denied();
  }, [readiness.phase, denied]);
  const capabilities = readiness.phase === "ready" ? readiness.value : null;
  useEffect(
    () => () => {
      selection.current++;
      operation.current?.abort();
    },
    [],
  );
  async function choose(file?: File) {
    const generation = ++selection.current;
    operation.current?.abort();
    setBusy(false);
    setIntent(null);
    setRow(null);
    setDownload(null);
    setMessage("");
    if (!file) return;
    try {
      const prepared = await prepareEvidence(file, versionId);
      if (selection.current === generation) setIntent(prepared);
    } catch {
      if (selection.current === generation)
        setMessage("Choose a PNG, JPEG or UTF-8 text file up to 10 MiB.");
    }
  }
  async function run(action: (signal: AbortSignal) => Promise<void>) {
    operation.current?.abort();
    const controller = new AbortController();
    operation.current = controller;
    setBusy(true);
    setMessage("");
    try {
      await action(controller.signal);
    } catch (error) {
      if (!controller.signal.aborted) {
        if (error instanceof ApiError && [401, 403].includes(error.status)) {
          setRow(null);
          setDownload(null);
          setIntent(null);
          denied();
        } else
          setMessage(
            "The outcome could not be confirmed. Retry the same action, or refresh saved evidence.",
          );
      }
    } finally {
      if (operation.current === controller) setBusy(false);
    }
  }
  return (
    <section
      className="governance-section"
      aria-label="Private evidence intake"
    >
      <h3>Attach creation or permission evidence</h3>
      <GovernanceRead state={readiness} query={config}>
        {(ready) => (
          <p role="status">
            Evidence upload{" "}
            {ready.upload_available ? "configured" : "unavailable"} · inspection{" "}
            {ready.inspection_available ? "configured" : "unavailable"}
          </p>
        )}
      </GovernanceRead>
      <p className="help">
        Private to the owner · this exact version · seven-day access expiry.
        Inspection does not establish ownership. Automatic deletion is
        unavailable until retention authority is configured.
      </p>
      <label>
        Evidence file
        <input
          type="file"
          accept="image/png,image/jpeg,text/plain"
          disabled={busy}
          onChange={(event) => void choose(event.target.files?.[0])}
        />
      </label>
      {intent && (
        <p>
          {intent.file.name} · {intent.file.size} bytes
        </p>
      )}
      <div className="button-row">
        <button
          className="primary"
          disabled={
            !intent || busy || row !== null || !capabilities?.upload_available
          }
          onClick={() =>
            void run(async (signal) => {
              if (intent) {
                const receipt = await gateway.upload(intent, signal);
                if (!signal.aborted) setRow(receipt);
              }
            })
          }
        >
          Upload private evidence
        </button>
        {row && (
          <button
            className="secondary"
            disabled={
              busy ||
              row.state !== "quarantined" ||
              !capabilities?.inspection_available
            }
            onClick={() =>
              void run(async (signal) => {
                const receipt = await gateway.inspect(row.id, signal);
                if (!signal.aborted) setRow(receipt);
              })
            }
          >
            Inspect evidence
          </button>
        )}
        {row?.state === "clean" && (
          <button
            className="secondary"
            disabled={busy || !capabilities?.download_available}
            onClick={() =>
              void run(async (signal) => {
                const blob = await gateway.download(row, signal);
                if (!signal.aborted) setDownload(blob);
              })
            }
          >
            Download inspected evidence
          </button>
        )}
        {busy && (
          <button
            className="secondary"
            onClick={() => {
              operation.current?.abort();
              setBusy(false);
              setMessage(
                "Request stopped. Its server outcome may still need reconciliation.",
              );
            }}
          >
            Stop request
          </button>
        )}
      </div>
      {row && (
        <p role="status">
          {row.state} · expires {row.expires_at} · evidence {row.id}
        </p>
      )}
      {message && <p role="alert">{message}</p>}
      {download && row?.state === "clean" && (
        <EvidenceDownload blob={download} id={row.id} />
      )}
      {row?.state === "clean" && registry && (
        <AssetEnrollment
          key={row.id}
          registry={registry}
          row={row}
          denied={denied}
        />
      )}
      {records && (
        <EvidenceLibrary
          records={records}
          gateway={gateway}
          registry={registry}
          versionId={versionId}
          denied={denied}
          purgeAvailable={capabilities?.purge_available ?? false}
        />
      )}
    </section>
  );
}
