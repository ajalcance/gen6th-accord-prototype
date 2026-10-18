import { useCallback } from "react";
import type {
  CreditGateway,
  CreditProfile,
  CreditSnapshot,
} from "../../lib/persona-credits";
import type { RecordWorkspaceProps } from "./record-journey";
import { useGovernanceRead } from "./saved-governance-read";
import { GovernanceRead, RecordedTime } from "./governance-common";
import {
  WriteFeedback,
  ReloadWrite,
  SubmitWriteForm,
} from "./prepared-write-common";
import { useWriteDraft } from "./prepared-write-state";
import { useCreditMutation } from "./credit-state";
import CreditEditor from "./credit-editor";

export default function PerformerCredits(props: RecordWorkspaceProps) {
  const gateway = props.source.credits;
  if (!gateway)
    return (
      <p className="help">
        Aliases and structured credits are unavailable on this connection.
      </p>
    );
  if (gateway.workspaceId !== props.source.workspaceId)
    return <p role="alert">The credit connection could not be validated.</p>;
  return <CreditRecords {...props} gateway={gateway} />;
}
function CreditRecords(
  props: RecordWorkspaceProps & { gateway: CreditGateway },
) {
  const { gateway, version } = props;
  const load = useCallback(
    (signal: AbortSignal) => gateway.read(version.version_id, signal),
    [gateway, version.version_id],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <section
      className="workflow-panel workflow-stack"
      aria-label="Aliases and contributor credits"
    >
      <div>
        <h2>Aliases &amp; contributor credits</h2>
        <p className="help">
          Visible to authorized members of this workspace. Confirmation accepts
          an attributed role; ownership and use permission remain separate.
        </p>
      </div>
      <GovernanceRead
        resource="Aliases and contributor credits"
        state={state}
        query={query}
      >
        {(profile) => (
          <>
            <CreditEntries
              {...props}
              profile={profile}
              reload={() => void query.retry()}
            />
            {props.source.writeGateway && (
              <CreditEditor
                {...props}
                profile={profile}
                reload={() => void query.retry()}
              />
            )}
          </>
        )}
      </GovernanceRead>
    </section>
  );
}
function CreditEntries(
  props: RecordWorkspaceProps & {
    gateway: CreditGateway;
    profile: CreditProfile;
    reload: () => void;
  },
) {
  const { snapshot, confirmations } = props.profile;
  if (!snapshot)
    return <p>No aliases or structured credits recorded for this version.</p>;
  return (
    <div className="credit-entries">
      <p>Aliases: {snapshot.content.aliases.join(" · ") || "None recorded"}</p>
      <p className="help">
        Declared by {snapshot.declared_by} ·{" "}
        <RecordedTime value={snapshot.recorded_at} />
      </p>
      {!snapshot.content.credits.length && (
        <p>No structured credits recorded.</p>
      )}
      {snapshot.content.credits.map((_, index) => (
        <CreditCard
          key={index}
          {...props}
          snapshot={snapshot}
          index={index}
          confirmations={confirmations}
        />
      ))}
      <p className="help">
        These annotations have their own receipts. Existing version reviews and
        passports do not certify or include these credits.
      </p>
    </div>
  );
}
function CreditCard(
  props: Parameters<typeof CreditConfirm>[0] & {
    confirmations: CreditProfile["confirmations"];
  },
) {
  const credit = props.snapshot.content.credits[props.index];
  const accepted = props.confirmations.find(
    (row) => row.credit_index === props.index,
  );
  return (
    <article className="governance-card">
      <div className="governance-heading">
        <h3>{credit.name}</h3>
        <span className="status neutral">
          {accepted ? "Contributor confirmed" : "Creator declared"}
        </span>
      </div>
      <p>
        {credit.role.replaceAll("_", " ")} · {credit.kind}
      </p>
      {accepted && (
        <p className="help">
          Confirmed by {accepted.actor_ref} ·{" "}
          <RecordedTime value={accepted.recorded_at} />
        </p>
      )}
      {credit.evidence_id && (
        <CreditEvidenceReference id={credit.evidence_id} />
      )}
      {credit.actor_ref && !accepted && (
        <details>
          <summary>Confirm my credited role</summary>
          <CreditConfirm {...props} />
        </details>
      )}
      {credit.kind === "organization" && (
        <p className="help">Organization attestation is not recorded.</p>
      )}
    </article>
  );
}
function CreditEvidenceReference({ id }: { id: string }) {
  return (
    <details>
      <summary>Supporting evidence reference</summary>
      <p>{id}</p>
      <p className="help">
        This reference does not share its attachment or establish its contents.
        Inspect authorized evidence in Evidence &amp; assets.
      </p>
    </details>
  );
}
function CreditConfirm(
  props: RecordWorkspaceProps & {
    gateway: CreditGateway;
    snapshot: CreditSnapshot;
    index: number;
    reload: () => void;
  },
) {
  const { source, version, gateway, snapshot, index, denied } = props;
  const key = `${source.workspaceId}:${source.sessionKey}:credit-confirm:${snapshot.id}:${index}`;
  const draft = useWriteDraft(key, {});
  const mutation = useCreditMutation(
    gateway,
    key,
    denied,
    snapshot.content.credits[index].actor_ref,
  );
  return (
    <>
      <p className="help">
        Only the account named in this credit can confirm it. Confirmation
        records this exact declaration at receipt time.
      </p>
      <SubmitWriteForm
        draft={draft}
        mutation={mutation}
        ready
        label="Confirm my contribution"
        confirmation="I confirm this credited role describes my contribution."
        submit={() =>
          void mutation.submit({
            request_id: crypto.randomUUID(),
            version_id: version.version_id,
            profile_id: snapshot.id,
            credit_index: index,
          })
        }
      >
        <span />
      </SubmitWriteForm>
      <WriteFeedback {...mutation} retry={() => void mutation.retry()} />
      <ReloadWrite
        draft={draft}
        mutation={mutation}
        loading={false}
        reload={props.reload}
        label="Reload credit receipts"
      />
    </>
  );
}
