import { useState } from "react";

export default function CopyReference({
  value,
  label,
}: {
  value: string;
  label: string;
}) {
  const [message, setMessage] = useState("");
  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setMessage(`${label} copied.`);
    } catch {
      setMessage("Copy unavailable. Select and copy the displayed value.");
    }
  }
  return (
    <span className="copy-reference">
      <code>{value}</code>
      <button
        type="button"
        className="text-button"
        aria-label={`Copy ${label}`}
        onClick={() => void copy()}
      >
        Copy
      </button>
      {message && (
        <span className="help" role="status">
          {message}
        </span>
      )}
    </span>
  );
}
