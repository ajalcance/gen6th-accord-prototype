import { useState, useEffect } from "react";
import type {
  PersonaVersion,
  CampaignReceipt,
} from "../../lib/persona-contracts";
import {
  publicFields,
  publicProjection,
  type PublicField,
  type ApprovalCommand,
  type PublicationGateway,
  type PublicationReceipt,
} from "../../lib/persona-publications";
import { usePersonaQuery } from "./use-persona-query";
import { GovernanceRead } from "./governance-common";
import { useGovernanceAccess } from "./saved-governance-read";
import { PassportDownload } from "./passport-package-result";
import PassportShare from "./passport-share";
import PublicationHistory from "./publication-history";

type Props = {
  gateway: PublicationGateway;
  version: PersonaVersion;
  offer: CampaignReceipt;
  eligible: boolean;
};
const requiredFields: PublicField[] = ["name", "ai_disclosure"];
function usePublication({ gateway, offer }: Props) {
  const [fields, setFields] = useState<PublicField[]>(requiredFields);
  const [confirmed, setConfirmed] = useState(false);
  const [intent, setIntent] = useState<ApprovalCommand | null>(null);
  const [withdrawn, setWithdrawn] = useState(false);
  const { state, query } = usePersonaQuery<PublicationReceipt>();
  useGovernanceAccess(state.phase);
  useEffect(() => () => query.stop(), [query]);
  function choose(field: PublicField, checked: boolean) {
    setConfirmed(false);
    setFields(
      checked ? [...fields, field] : fields.filter((value) => value !== field),
    );
  }
  function prepare() {
    const command = intent ?? {
      request_id: crypto.randomUUID(),
      campaign_id: offer.id,
      fields,
    };
    setIntent(command);
    void query.run((signal) => gateway.approve(command, signal));
  }
  function withdraw(receipt: PublicationReceipt) {
    void query.run(async (signal) => {
      const result = await gateway.unpublish(receipt.publication_id, signal);
      if (!signal.aborted) setWithdrawn(true);
      return result;
    });
  }
  function reset() {
    query.clear();
    setIntent(null);
    setConfirmed(false);
    setWithdrawn(false);
  }
  return {
    fields,
    confirmed,
    setConfirmed,
    intent,
    withdrawn,
    state,
    query,
    choose,
    prepare,
    withdraw,
    reset,
  };
}
type PublicationState = ReturnType<typeof usePublication>;
export default function PassportPublication(props: Props) {
  const model = usePublication(props);
  return (
    <section aria-label="Approved public passport">
      <h3>Public passport preview</h3>
      <p className="help">
        Approve only the fields shown below. Private evidence, recipient
        identifiers and the private export stay excluded. Public access also
        requires the operator’s publication activation.
      </p>
      <div className="public-approval-layout">
        <PublicFields model={model} />
        <RecipientPreview {...props} fields={model.fields} />
      </div>
      <ApprovalControls {...props} model={model} />
      <PublicationResult model={model} />
      {model.intent && model.state.phase !== "loading" && (
        <button onClick={model.reset}>Start a new field approval</button>
      )}
      <PublicationHistory gateway={props.gateway} campaign={props.offer.id} />
    </section>
  );
}
function PublicFields({ model }: { model: PublicationState }) {
  return (
    <fieldset disabled={model.intent !== null}>
      <legend>Fields approved for public visibility</legend>
      {publicFields.map((field) => (
        <label key={field}>
          <input
            type="checkbox"
            checked={model.fields.includes(field)}
            disabled={requiredFields.includes(field)}
            onChange={(event) => model.choose(field, event.target.checked)}
          />
          {field.replaceAll("_", " ")}
        </label>
      ))}
    </fieldset>
  );
}
function RecipientPreview({
  version,
  offer,
  fields,
}: Props & { fields: PublicField[] }) {
  const preview: Partial<Record<PublicField, string>> = {
    ...version.content,
    production_name: offer.scope.production?.title ?? offer.scope.name,
    purpose: offer.scope.purpose,
    conditions: offer.scope.conditions,
    portrait_sha256:
      "Saved inspected portrait thumbnail (explicit public approval)",
  };
  return (
    <section
      className="public-recipient-preview"
      aria-label="Public recipient preview"
    >
      <h4>Recipient preview</h4>
      <dl className="saved-fields">
        {fields.map((field) => (
          <div key={field}>
            <dt>{field.replaceAll("_", " ")}</dt>
            <dd>{preview[field]}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
function ApprovalControls({
  version,
  offer,
  eligible,
  model,
}: Props & { model: PublicationState }) {
  return (
    <>
      <p>
        Version {version.revision} · scope {offer.scope.starts_at} to{" "}
        {offer.scope.ends_at}. Statements remain creator claims.
      </p>
      <label>
        <input
          type="checkbox"
          checked={model.confirmed}
          disabled={model.intent !== null}
          onChange={(event) => model.setConfirmed(event.target.checked)}
        />
        I approve these fields, version and scope dates for public disclosure.
        Copies downloaded by others cannot be recalled.
      </label>
      <button
        disabled={
          !eligible ||
          !model.confirmed ||
          model.state.phase === "loading" ||
          model.state.phase === "ready"
        }
        onClick={model.prepare}
      >
        {model.intent
          ? "Retry approved passport preparation"
          : "Prepare approved public passport"}
      </button>
    </>
  );
}
function PublicationResult({ model }: { model: PublicationState }) {
  return (
    <GovernanceRead state={model.state} query={model.query}>
      {(receipt) => (
        <>
          <p role="status">
            {model.withdrawn
              ? "Public access withdrawn"
              : `Public approval recorded for ${publicProjection(receipt.package).values.name}`}
          </p>
          {!model.withdrawn && (
            <>
              <PassportShare path={receipt.path} />
              <PassportDownload package_={receipt.package} />
              <button onClick={() => model.withdraw(receipt)}>
                Withdraw public access
              </button>
            </>
          )}
        </>
      )}
    </GovernanceRead>
  );
}
