import { useCallback, useState } from "react";
import type {
  CampaignReceipt,
  PersonaVersion,
} from "../../lib/persona-contracts";
import type { PersonaGateway } from "../../lib/persona-gateway";
import { GovernanceRead, RecordedTime } from "./governance-common";
import { DiscoveryPager, useGovernanceRead } from "./saved-governance-read";
import { CampaignRecord } from "./saved-governance-campaigns";

type Props = { gateway: PersonaGateway; version: PersonaVersion };
export default function ProductionHistory({ gateway, version }: Props) {
  const [cursor, setCursor] = useState<string | null>(null);
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
    <section className="workflow-stack" aria-label="Production history">
      <div>
        <h3>Productions &amp; appearances</h3>
        <p className="help">
          Recorded proposals for version {version.revision}, within your
          permitted scope. Select another saved version to inspect its history.
          Permission and evidence of an actual appearance are separate.
        </p>
      </div>
      <GovernanceRead resource="Production history" state={state} query={query}>
        {(page) => (
          <>
            {!page.items.length && <p>No production proposals on this page.</p>}
            {page.items.map((offer) => (
              <ProductionEntry
                key={offer.id}
                gateway={gateway}
                version={version}
                offer={offer}
              />
            ))}
          </>
        )}
      </GovernanceRead>
      <DiscoveryPager
        noun="productions"
        cursor={cursor}
        ready={state.phase === "ready"}
        next={state.phase === "ready" ? state.value.next_after_id : null}
        change={(value) => {
          query.clear();
          setCursor(value as string | null);
        }}
      />
    </section>
  );
}
function ProductionEntry({
  gateway,
  version,
  offer,
}: Props & { offer: CampaignReceipt }) {
  const [expanded, setExpanded] = useState(false);
  const production = offer.scope.production;
  return (
    <article className="governance-card production-entry">
      <div className="governance-heading">
        <h3>{production?.title ?? offer.scope.name}</h3>
        <span className="status neutral">Offer recorded</span>
      </div>
      <ProductionFacts offer={offer} />
      <p className="help">
        An offer or accepted scope does not prove the performer appeared in a
        released production. No appearance attestation is recorded by this
        workflow.
      </p>
      <details onToggle={(event) => setExpanded(event.currentTarget.open)}>
        <summary>
          Inspect current permission, assets &amp; decision history
        </summary>
        {expanded && (
          <CampaignRecord
            gateway={gateway}
            revision={version.revision}
            offer={offer}
          />
        )}
      </details>
    </article>
  );
}
function ProductionFacts({ offer }: { offer: CampaignReceipt }) {
  const production = offer.scope.production;
  return (
    <dl className="governance-fields governance-columns">
      {production && (
        <>
          <div>
            <dt>Episode</dt>
            <dd>{production.episode}</dd>
          </div>
          <div>
            <dt>Character / role</dt>
            <dd>{production.role_name}</dd>
          </div>
        </>
      )}
      <div>
        <dt>Submitted by</dt>
        <dd>{offer.owner_ref}</dd>
      </div>
      <div>
        <dt>Recipient</dt>
        <dd>{offer.scope.recipient_ref}</dd>
      </div>
      <div>
        <dt>Recorded</dt>
        <dd>
          <RecordedTime value={offer.recorded_at} />
        </dd>
      </div>
      <div>
        <dt>Referenced assets</dt>
        <dd>{offer.assets.length}</dd>
      </div>
    </dl>
  );
}
