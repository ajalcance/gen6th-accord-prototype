import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../lib/api-client";
import type {
  AssetRegistry,
  AssetEnrollmentCommand,
  AssetEnrollmentReceipt,
} from "../../lib/persona-assets";
import type { EvidenceStatus } from "../../lib/persona-read-contracts";

export default function AssetEnrollment({
  registry,
  row,
  denied,
}: {
  registry: AssetRegistry;
  row: EvidenceStatus;
  denied: () => void;
}) {
  const [label, setLabel] = useState(""),
    [statement, setStatement] = useState(""),
    [confirmed, setConfirmed] = useState(false);
  const [intent, setIntent] = useState<AssetEnrollmentCommand | null>(null);
  const [receipt, setReceipt] = useState<AssetEnrollmentReceipt | null>(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const operation = useRef<AbortController | null>(null);
  useEffect(() => () => operation.current?.abort(), []);
  async function enroll() {
    const command = intent ?? {
      request_id: crypto.randomUUID(),
      version_id: row.version_id,
      evidence_id: row.id,
      label,
      permission_statement: statement,
    };
    setIntent(command);
    setBusy(true);
    setError("");
    const controller = new AbortController();
    operation.current = controller;
    try {
      const result = await registry.enroll(command, controller.signal);
      if (!controller.signal.aborted) setReceipt(result);
    } catch (failure) {
      if (!controller.signal.aborted) {
        if (failure instanceof ApiError && [401, 403].includes(failure.status))
          denied();
        else
          setError(
            "Enrollment outcome unavailable. Retry the same intent or reload the production asset catalogue.",
          );
      }
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  const locked = intent !== null;
  return (
    <section aria-label="Enroll production asset">
      <h4>Register these inspected bytes as a production asset</h4>
      <p className="help">
        A separate owner statement is required. Registration records your claim;
        it does not grant use permission. The original remains private and
        expires after seven days.
      </p>
      <label>
        Asset label
        <input
          value={label}
          placeholder="A short name for these inspected bytes."
          maxLength={80}
          disabled={locked}
          onChange={(e) => setLabel(e.target.value)}
        />
      </label>
      <label>
        Permission or licence basis
        <textarea
          value={statement}
          placeholder="Explain the permission or licence that supports registration."
          maxLength={500}
          disabled={locked}
          onChange={(e) => setStatement(e.target.value)}
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={confirmed}
          disabled={locked}
          onChange={(e) => setConfirmed(e.target.checked)}
        />
        I am authorized to register these bytes for this version. Clearance will
        still require review and recipient acceptance.
      </label>
      <button
        disabled={
          busy ||
          receipt !== null ||
          !confirmed ||
          !label.trim() ||
          !statement.trim()
        }
        onClick={() => void enroll()}
      >
        {intent && !receipt
          ? "Retry asset enrollment"
          : "Register production asset"}
      </button>
      {receipt && (
        <p role="status">
          Registered {receipt.asset.label} · {receipt.asset.id}. Reload
          production assets before preparing the offer.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
