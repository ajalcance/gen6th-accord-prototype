import { useEffect, useRef } from "react";
import type {
  PassportVerification,
  SignedPassport,
} from "../../lib/persona-passport-contracts";

export function PassportDownload({ package_ }: { package_: SignedPassport }) {
  const download = useRef<HTMLAnchorElement>(null);
  const content = JSON.stringify(package_, null, 2);
  useEffect(() => {
    const next = URL.createObjectURL(
      new Blob([content], { type: "application/json" }),
    );
    download.current?.setAttribute("href", next);
    return () => URL.revokeObjectURL(next);
  }, [content]);
  return (
    <section aria-label="Signed passport package">
      <h4>Signed package prepared</h4>
      <p>
        Key version: {package_.key_id}. Keep the package with the approved
        production assets.
      </p>
      <a ref={download} download="accord-persona-passport.json">
        Download passport JSON
      </a>
      <details className="export-preview">
        <summary>Inspect signed contents</summary>
        <pre>{content}</pre>
      </details>
      <p className="help">
        A signature binds these contents to a trusted platform key. It does not
        establish legal rights or continuing permission.
      </p>
    </section>
  );
}
const integrityLabels: Record<PassportVerification["integrity"], string> = {
  valid: "Signature valid · package matches saved production",
  invalid_signature: "Altered package or invalid signature",
  untrusted_key: "Signing key is not trusted",
  invalid_package: "Signed contents do not form a valid passport",
  binding_mismatch: "Package does not match this saved production",
};
export function PassportVerificationResult({
  result,
}: {
  result: PassportVerification;
}) {
  const status = result.current_status;
  return (
    <section aria-label="Passport verification result" role="status">
      <h4>{integrityLabels[result.integrity]}</h4>
      {status && (
        <>
          <p>
            {status.eligible_for_use
              ? "Recorded production scope eligible at verification"
              : "Current production use blocked"}
          </p>
          <p>Permission checked at {status.evaluated_at}.</p>
          {status.blocking_reasons.length > 0 && (
            <ul>
              {status.blocking_reasons.map((reason) => (
                <li key={reason}>{reason.replaceAll("_", " ")}</li>
              ))}
            </ul>
          )}
        </>
      )}
      <p className="help">
        Check permission again before use. Integrity, identity and legal rights
        are separate questions.
      </p>
    </section>
  );
}
