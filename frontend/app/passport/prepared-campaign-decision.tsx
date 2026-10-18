import { useCallback } from "react";
import type {
  CampaignReceipt,
  DecisionCommand,
  PersonaVersion,
} from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { useGovernanceRead } from "./saved-governance-read";
import { GovernanceRead } from "./governance-common";
import { usePreparedWrite, useWriteDraft } from "./prepared-write-state";
import {
  writeKey,
  WriteFeedback,
  ReloadWrite,
  SubmitWriteForm,
  DecisionFields,
  type WriteDraftState,
} from "./prepared-write-common";

type Props = {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
};
export default function PreparedCampaignDecision({
  source,
  version,
  denied,
}: Props) {
  const load = useCallback(
    (signal: AbortSignal) =>
      source.gateway.governance.campaigns(
        version.version_id,
        { after_id: null, limit: 20 },
        signal,
      ),
    [source.gateway, version.version_id],
  );
  const { state, query } = useGovernanceRead(load);
  const draft = useWriteDraft(writeKey(source, "decide", version.version_id), {
    campaign: "",
  });
  return (
    <section aria-label="Decide a scoped campaign">
      <h3>Campaign decision · version {version.revision}</h3>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <CampaignSelection
            items={page.items}
            draft={draft}
            source={source}
            denied={denied}
          />
        )}
      </GovernanceRead>
      <button
        className="secondary"
        disabled={state.phase === "loading"}
        onClick={() => void query.run(load)}
      >
        Reload campaign offers
      </button>
    </section>
  );
}
function CampaignSelection({
  items,
  draft,
  source,
  denied,
}: {
  items: CampaignReceipt[];
  draft: WriteDraftState;
  source: SavedPersonaSource;
  denied: () => void;
}) {
  const offer =
    items.find((row) => row.id === draft.fields.campaign) ?? items[0];
  if (!offer)
    return (
      <p>
        No visible campaign on this page. Reload after an authorized offer is
        recorded.
      </p>
    );
  return (
    <>
      <label>
        Decision campaign
        <select
          value={offer.id}
          onChange={(event) => draft.change("campaign", event.target.value)}
        >
          {items.map((row) => (
            <option key={row.id} value={row.id}>
              {row.scope.name} · {row.scope.recipient_ref}
            </option>
          ))}
        </select>
      </label>
      <DecisionForm
        key={offer.id}
        source={source}
        offer={offer}
        denied={denied}
      />
    </>
  );
}
type DecisionProps = {
  source: SavedPersonaSource;
  offer: CampaignReceipt;
  denied: () => void;
};
function useDecisionWrite({ source, offer, denied }: DecisionProps) {
  const key = writeKey(source, "decide", offer.id);
  const draft = useWriteDraft(key, {
    decision: "changes_requested",
    statement: "",
    confirm: "",
  });
  const mutation = usePreparedWrite(
    source.writeGateway!,
    "decide",
    key,
    denied,
  );
  const load = useCallback(
    (signal: AbortSignal) => source.gateway.campaignStatus(offer.id, signal),
    [source.gateway, offer.id],
  );
  const read = useGovernanceRead(load);
  const submit = (previous: string | null) =>
    void mutation.submit({
      request_id: crypto.randomUUID(),
      campaign_id: offer.id,
      expected_previous_id: previous,
      decision: draft.fields.decision as DecisionCommand["decision"],
      statement: draft.fields.statement,
    });
  return { draft, mutation, load, ...read, submit };
}
function DecisionForm(props: DecisionProps) {
  const action = useDecisionWrite(props),
    { draft, mutation, load, state, query } = action;
  return (
    <>
      <CampaignSummary offer={props.offer} />
      <GovernanceRead state={state} query={query}>
        {(status) => (
          <SubmitWriteForm
            draft={draft}
            mutation={mutation}
            ready={!!draft.fields.statement?.trim()}
            label="Record campaign decision"
            confirmation="I reviewed this named recipient, exact version, assets, conditions and duration."
            submit={() => action.submit(status.latest_decision?.id ?? null)}
          >
            <DecisionFields draft={draft} campaign />
          </SubmitWriteForm>
        )}
      </GovernanceRead>
      <WriteFeedback {...mutation} retry={() => void mutation.retry()} />
      <ReloadWrite
        draft={draft}
        mutation={mutation}
        loading={state.phase === "loading"}
        reload={() => void query.run(load)}
        label="Reload campaign before a new intent"
      />
    </>
  );
}
function CampaignSummary({ offer }: { offer: CampaignReceipt }) {
  const fields = [
    ["Recipient", offer.scope.recipient_ref],
    ["Purpose", offer.scope.purpose],
    ["Conditions", offer.scope.conditions],
    ["Duration", offer.scope.starts_at + " → " + offer.scope.ends_at],
  ];
  return (
    <article className="governance-card">
      <h4>{offer.scope.name}</h4>
      <dl className="governance-fields governance-columns">
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <ul>
        {offer.assets.map((asset) => (
          <li key={asset.id}>{asset.label}</li>
        ))}
      </ul>
      <p className="help">
        Saved campaign · version-bound scope. The server rechecks the current
        actor, version, review and scope for every decision.
      </p>
    </article>
  );
}
