import { useCallback, useState } from "react";
import type {
  CampaignReceipt,
  PersonaVersion,
} from "../../lib/persona-contracts";
import type { PassportGateway } from "../../lib/persona-passports";
import type {
  PassportVerification,
  SignedPassport,
} from "../../lib/persona-passport-contracts";
import { GovernanceRead } from "./governance-common";
import {
  useGovernanceAccess,
  useGovernanceRead,
} from "./saved-governance-read";
import { usePersonaQuery } from "./use-persona-query";
import {
  PassportPackageInput,
  usePassportInput,
} from "./passport-package-input";
import {
  PassportDownload,
  PassportVerificationResult,
} from "./passport-package-result";

type Props = {
  gateway: PassportGateway;
  version: PersonaVersion;
  offer: CampaignReceipt;
  eligible: boolean;
  mode?: "issue" | "verify" | "all";
  onPrepared?: (packet: SignedPassport | null) => void;
};
export default function PassportActions(props: Props) {
  const load = useCallback(
    (signal: AbortSignal) => props.gateway.readiness(signal),
    [props.gateway],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <section aria-label="Passport integrity controls">
      <h3>
        {props.mode === "issue"
          ? "Private passport issuance"
          : props.mode === "verify"
            ? "Verify a passport package"
            : "Passport export & verification"}
      </h3>
      <GovernanceRead state={state} query={query}>
        {(ready) => (
          <>
            {!ready.export_available && props.mode !== "verify" && (
              <p>Passport signing is not configured on this connection.</p>
            )}
            {!ready.verification_available && props.mode !== "issue" && (
              <p>
                Trusted verification keys are not configured on this connection.
              </p>
            )}
            {props.mode !== "verify" && (
              <ExportPassport {...props} available={ready.export_available} />
            )}
            {props.mode !== "issue" && (
              <VerifyPassport
                gateway={props.gateway}
                offer={props.offer}
                available={ready.verification_available}
              />
            )}
          </>
        )}
      </GovernanceRead>
    </section>
  );
}
function ExportPassport({
  gateway,
  version,
  offer,
  eligible,
  available,
  onPrepared,
}: Props & { available: boolean }) {
  const [confirmed, setConfirmed] = useState(false);
  const { state, query } = usePersonaQuery<SignedPassport>();
  useGovernanceAccess(state.phase);
  const canExport = available && eligible && !!offer.scope.production;
  return (
    <section aria-label="Export production passport">
      <label>
        <input
          type="checkbox"
          checked={confirmed}
          disabled={!canExport || state.phase === "loading"}
          onChange={(event) => {
            query.clear();
            onPrepared?.(null);
            setConfirmed(event.target.checked);
          }}
        />
        Share this exact version, production scope, approved reference hashes
        and submitted reference IDs in the signed package.
      </label>
      <button
        disabled={!canExport || !confirmed || state.phase === "loading"}
        onClick={() => {
          onPrepared?.(null);
          void query.run(async (signal) => {
            const packet = await gateway.export(version, offer, signal);
            if (!signal.aborted) onPrepared?.(packet);
            return packet;
          });
        }}
      >
        Prepare signed passport
      </button>
      <PassportExportNotice eligible={eligible} offer={offer} />
      <GovernanceRead state={state} query={query}>
        {(package_) => <PassportDownload package_={package_} />}
      </GovernanceRead>
    </section>
  );
}
function VerifyPassport({
  gateway,
  offer,
  available,
}: {
  gateway: PassportGateway;
  offer: CampaignReceipt;
  available: boolean;
}) {
  const { state, query } = usePersonaQuery<PassportVerification>();
  const input = usePassportInput(query.clear.bind(query));
  useGovernanceAccess(state.phase);
  function verify() {
    const package_ = input.prepare();
    if (package_)
      void query.run((signal) => gateway.verify(offer.id, package_, signal));
  }
  return (
    <section aria-label="Verify saved production passport">
      <PassportPackageInput
        input={input}
        disabled={!available || state.phase === "loading"}
      />
      <button
        disabled={!available || !input.value || state.phase === "loading"}
        onClick={verify}
      >
        Verify passport package
      </button>
      <GovernanceRead state={state} query={query}>
        {(result) => <PassportVerificationResult result={result} />}
      </GovernanceRead>
    </section>
  );
}

function PassportExportNotice({
  eligible,
  offer,
}: Pick<Props, "eligible" | "offer">) {
  return (
    <>
      {!eligible && (
        <p>Current accepted production permission is required for export.</p>
      )}
      {!offer.scope.production && (
        <p>
          This campaign has no named production. Prepare a production offer to
          issue its passport.
        </p>
      )}
    </>
  );
}
