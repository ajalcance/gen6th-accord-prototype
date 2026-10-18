import { useCallback, useState } from "react";
import type {
  CampaignReceipt,
  CampaignStatus,
  DecisionReceipt,
  PersonaVersion,
} from "../../lib/persona-contracts";
import type { PersonaGateway } from "../../lib/persona-gateway";
import { requireContract } from "../../lib/persona-validation";
import {
  GovernanceEmpty,
  GovernanceRead,
  HistoryPager,
  RecordedTime,
} from "./governance-common";
import { DecisionRow } from "./campaign-decision-row";
import GovernanceAudit from "./governance-audit";
import { DiscoveryPager, useGovernanceRead } from "./saved-governance-read";
import { SavedProductionUse } from "./production-use-fields";

type Props = { gateway: PersonaGateway; version: PersonaVersion };
export default function SavedGovernanceCampaigns({ gateway, version }: Props) {
  const [cursor, setCursor] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const load = useCallback(
    (signal: AbortSignal) =>
      gateway.governance.campaigns(
        version.version_id,
        { after_id: cursor, limit: 20 },
        signal,
      ),
    [gateway, version.version_id, cursor],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <section
      className="governance-section"
      aria-label="Saved campaign decisions"
    >
      <h3>Production offers</h3>
      <p className="help">
        Offers visible to the owner or named recipient. An offer alone does not
        authorize use.
      </p>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <CampaignSelection
            items={page.items}
            selected={selected}
            change={setSelected}
            gateway={gateway}
            revision={version.revision}
          />
        )}
      </GovernanceRead>
      <DiscoveryPager
        noun="campaigns"
        cursor={cursor}
        ready={state.phase === "ready"}
        next={state.phase === "ready" ? state.value.next_after_id : null}
        change={(value) => {
          query.clear();
          setSelected(null);
          setCursor(value as string | null);
        }}
      />
    </section>
  );
}

function CampaignSelection({
  items,
  selected,
  change,
  gateway,
  revision,
}: {
  items: CampaignReceipt[];
  selected: string | null;
  change: (value: string) => void;
  gateway: PersonaGateway;
  revision: number;
}) {
  if (items.length === 0)
    return (
      <GovernanceEmpty title="No campaigns on this page">
        Return to the first page, or prepare a scoped offer after independent
        review through a verified workflow.
      </GovernanceEmpty>
    );
  const offer = items.find((row) => row.id === selected) ?? items[0];
  return (
    <>
      <label>
        Campaign
        <select
          value={offer.id}
          onChange={(event) => change(event.target.value)}
        >
          {items.map((row) => (
            <option key={row.id} value={row.id}>
              {row.scope.name} · {row.scope.recipient_ref}
            </option>
          ))}
        </select>
      </label>
      <CampaignRecord
        key={offer.id}
        gateway={gateway}
        revision={revision}
        offer={offer}
      />
    </>
  );
}

export function CampaignRecord({
  gateway,
  revision,
  offer,
}: {
  gateway: PersonaGateway;
  revision: number;
  offer: CampaignReceipt;
}) {
  const load = useCallback(
    async (signal: AbortSignal) => {
      const status = await gateway.campaignStatus(offer.id, signal);
      requireContract(JSON.stringify(status.receipt) === JSON.stringify(offer));
      return status;
    },
    [gateway, offer],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <GovernanceRead state={state} query={query}>
      {(status) => (
        <>
          <SavedCampaignScope status={status} revision={revision} />
          <GovernanceAudit
            gateway={gateway}
            binding={{
              recordId: offer.id,
              kind: "campaign_offer",
              versionId: offer.version_id,
              actor: offer.owner_ref,
              eventId: offer.event_id,
              recordedAt: offer.recorded_at,
            }}
          />
          <SavedCampaignHistory gateway={gateway} offer={offer} />
        </>
      )}
    </GovernanceRead>
  );
}

const reasonLabels: Record<CampaignStatus["blocking_reasons"][number], string> =
  {
    stale_version: "A newer version exists",
    review_changed: "Independent review changed",
    reviewer_permission_removed: "Reviewer permission removed",
    owner_permission_removed: "Owner permission removed",
    recipient_permission_removed: "Recipient permission removed",
    awaiting_acceptance: "Awaiting recipient acceptance",
    changes_requested: "Recipient requested changes",
    revoked: "Owner revoked permission",
    not_started: "Time window has not started",
    expired: "Time window expired",
    supporting_evidence_unavailable:
      "Supporting evidence expired or is unavailable",
    lifecycle_unavailable: "Lifecycle policy is unavailable on this connection",
    performer_suspended: "Performer suspended by an independent reviewer",
    governance_missing: "Operator and rights declaration needed",
    governance_changed:
      "Declaration or responsible operator changed; prepare a new offer",
    operator_unavailable: "Responsible operator no longer has workspace access",
    governance_review_required:
      "Separate authority, rights and content assessments needed",
    governance_expired: "Assessments do not cover the full permission window",
    rights_window_unavailable: "Rights do not cover the full permission window",
    voice_rights_missing: "Voice use needs a declared voice right",
  };
function SavedCampaignScope({
  status,
  revision,
}: {
  status: CampaignStatus;
  revision: number;
}) {
  const scope = status.receipt.scope;
  return (
    <article className="governance-card">
      <div className="governance-heading">
        <h3>{scope.name}</h3>
        <span
          className={`status ${status.eligible_for_use ? "neutral" : "warning"}`}
        >
          {status.eligible_for_use ? "Recorded scope eligible" : "Use blocked"}
        </span>
      </div>
      <p className="help">
        Version {revision} · evaluated{" "}
        <RecordedTime value={status.evaluated_at} /> · no live rights or signing
        established.
      </p>
      {status.blocking_reasons.length > 0 && (
        <ul>
          {status.blocking_reasons.map((reason) => (
            <li key={reason}>{reasonLabels[reason]}</li>
          ))}
        </ul>
      )}
      <CampaignFields status={status} />
      <SavedProductionUse scope={scope} />
    </article>
  );
}

function CampaignFields({ status }: { status: CampaignStatus }) {
  const scope = status.receipt.scope;
  return (
    <>
      <dl className="governance-fields governance-columns">
        <div>
          <dt>Recipient</dt>
          <dd>{scope.recipient_ref}</dd>
        </div>
        <div>
          <dt>Purpose</dt>
          <dd>{scope.purpose}</dd>
        </div>
        <div>
          <dt>Conditions</dt>
          <dd>{scope.conditions}</dd>
        </div>
        <div>
          <dt>Time window</dt>
          <dd>
            <RecordedTime value={scope.starts_at} /> →{" "}
            <RecordedTime value={scope.ends_at} />
          </dd>
        </div>
      </dl>
      <details>
        <summary>Referenced assets & review</summary>
        <dl className="governance-fields">
          <div>
            <dt>Review ID</dt>
            <dd>{status.receipt.review_id}</dd>
          </div>
          {status.receipt.assets.map((asset) => (
            <div key={asset.id}>
              <dt>{asset.label}</dt>
              <dd>{asset.digest}</dd>
            </div>
          ))}
        </dl>
        <p className="help">
          Campaign assets are separate from temporary private evidence.
        </p>
      </details>
    </>
  );
}

function SavedCampaignHistory({
  gateway,
  offer,
}: {
  gateway: PersonaGateway;
  offer: CampaignReceipt;
}) {
  const [cursor, setCursor] = useState<number | null>(null);
  const load = useCallback(
    (signal: AbortSignal) =>
      gateway.reads.campaignHistory(
        offer.id,
        { before_ordinal: cursor, limit: 20 },
        signal,
      ),
    [gateway, offer.id, cursor],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <section className="governance-section" aria-label="Saved campaign history">
      <h3>Decision history</h3>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <SavedDecisionItems
            items={page.items}
            gateway={gateway}
            versionId={offer.version_id}
          />
        )}
      </GovernanceRead>
      <HistoryPager
        cursor={cursor}
        state={state}
        setCursor={(value) => {
          query.clear();
          setCursor(value);
        }}
        noun="decisions"
      />
    </section>
  );
}

function SavedDecisionItems({
  items,
  gateway,
  versionId,
}: {
  items: DecisionReceipt[];
  gateway: PersonaGateway;
  versionId: string;
}) {
  return (
    <>
      {items.length === 0 && (
        <GovernanceEmpty title="No campaign decisions">
          Recipient acceptance is still required for campaign eligibility.
        </GovernanceEmpty>
      )}
      {items.map((row) => (
        <DecisionRow
          key={row.id}
          gateway={gateway}
          row={row}
          versionId={versionId}
        />
      ))}
    </>
  );
}
