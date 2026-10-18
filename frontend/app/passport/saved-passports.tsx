import { useCallback, useState } from "react";
import type {
  CampaignReceipt,
  PersonaVersion,
} from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { GovernanceRead } from "./governance-common";
import { DiscoveryPager, useGovernanceRead } from "./saved-governance-read";
import { SavedProductionUse } from "./production-use-fields";
import PassportActions from "./passport-actions";
import PassportPublication from "./passport-publication";
import { requireContract } from "../../lib/persona-validation";
import WorkspaceSections from "./workspace-sections";
import PassportBooklet from "./passport-booklet";
import type { SignedPassport } from "../../lib/persona-passport-contracts";

export default function SavedPassports({
  source,
  version,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
}) {
  return (
    <PassportWorkspace
      key={`${source.workspaceId}:${source.sessionKey}:${version.version_id}`}
      source={source}
      version={version}
    />
  );
}
type WorkspaceProps = { source: SavedPersonaSource; version: PersonaVersion };
function PassportWorkspace({ source, version }: WorkspaceProps) {
  const model = usePassportWorkspace(source, version);
  return (
    <section
      className="workflow-panel workflow-stack"
      aria-label="Production passports"
    >
      <PassportHeading />
      {model.state.phase !== "denied" && (
        <PassportBooklet
          key={model.offer?.id ?? "no-offer"}
          source={source}
          version={version}
          offer={model.offer}
          packet={model.packet}
          disabled={model.state.phase !== "ready"}
        />
      )}
      <PassportOfferControls source={source} version={version} model={model} />
    </section>
  );
}
function PassportOfferControls({
  source,
  version,
  model,
}: WorkspaceProps & { model: ReturnType<typeof usePassportWorkspace> }) {
  return (
    <>
      <GovernanceRead
        state={model.state}
        query={model.query}
        resource="Production scopes"
      >
        {(page) => (
          <ProductionOfferSelection
            items={page.items}
            selected={model.selected}
            change={model.selectOffer}
            onPrepared={model.setPacket}
            source={source}
            version={version}
          />
        )}
      </GovernanceRead>
      <DiscoveryPager
        noun="production offers"
        cursor={model.cursor}
        ready={model.state.phase === "ready"}
        next={
          model.state.phase === "ready" ? model.state.value.next_after_id : null
        }
        change={model.changePage}
      />
    </>
  );
}
function PassportHeading() {
  return (
    <>
      <h3>Production scope</h3>
      <p>
        Choose this performer’s production scope. Verify current permission
        before use.
      </p>
    </>
  );
}
function ProductionOfferSelection({
  items,
  selected,
  change,
  source,
  version,
  onPrepared,
}: {
  items: CampaignReceipt[];
  selected: string | null;
  change: (id: string) => void;
  source: SavedPersonaSource;
  version: PersonaVersion;
  onPrepared: (packet: SignedPassport | null) => void;
}) {
  const offer = items.find((row) => row.id === selected) ?? items[0];
  if (!offer)
    return (
      <p>
        No production offers for this version. Record a scoped offer and
        recipient decision first.
      </p>
    );
  return (
    <>
      <label>
        Production offer
        <select
          value={offer.id}
          onChange={(event) => change(event.target.value)}
        >
          {items.map((row) => (
            <option key={row.id} value={row.id}>
              {row.scope.name}
            </option>
          ))}
        </select>
      </label>
      <PassportRecord
        key={offer.id}
        source={source}
        version={version}
        offer={offer}
        onPrepared={onPrepared}
      />
    </>
  );
}
function PassportRecord({
  source,
  version,
  offer,
  onPrepared,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
  offer: CampaignReceipt;
  onPrepared: (packet: SignedPassport | null) => void;
}) {
  const [section, setSection] = useState("Private issuance");
  const load = useCallback(
    async (signal: AbortSignal) => {
      const status = await source.gateway.campaignStatus(offer.id, signal);
      requireContract(JSON.stringify(status.receipt) === JSON.stringify(offer));
      return status;
    },
    [source.gateway, offer],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <GovernanceRead state={state} query={query}>
      {(status) => (
        <>
          <SavedProductionUse scope={status.receipt.scope} />
          <p>
            {status.eligible_for_use
              ? "Recorded scope eligible at last check"
              : "Production use blocked"}
          </p>
          <button className="secondary" onClick={() => void query.run(load)}>
            Refresh production permission
          </button>
          <PassportSections
            {...{ source, version, section }}
            select={setSection}
            offer={status.receipt}
            eligible={status.eligible_for_use}
            onPrepared={onPrepared}
          />
        </>
      )}
    </GovernanceRead>
  );
}
function PassportSections({
  source,
  version,
  offer,
  eligible,
  section,
  select,
  onPrepared,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
  offer: CampaignReceipt;
  eligible: boolean;
  section: string;
  select: (section: string) => void;
  onPrepared: (packet: SignedPassport | null) => void;
}) {
  return (
    <>
      <WorkspaceSections
        items={["Private issuance", "Public sharing", "Verify package"]}
        selected={section}
        select={select}
        label="Passport sections"
      />
      {section !== "Public sharing" &&
        (source.passports ? (
          <PassportActions
            key={section}
            mode={section === "Private issuance" ? "issue" : "verify"}
            gateway={source.passports}
            version={version}
            offer={offer}
            eligible={eligible}
            onPrepared={onPrepared}
          />
        ) : (
          <p>Passport services are unavailable on this connection.</p>
        ))}
      {section === "Public sharing" && (
        <PublicPassportSection
          source={source}
          version={version}
          offer={offer}
          eligible={eligible}
        />
      )}
    </>
  );
}

function usePassportWorkspace(
  source: SavedPersonaSource,
  version: PersonaVersion,
) {
  const [cursor, setCursor] = useState<string | null>(null),
    [selected, setSelected] = useState<string | null>(null);
  const [packet, setPacket] = useState<SignedPassport | null>(null);
  const load = useCallback(
    (signal: AbortSignal) =>
      source.gateway.governance.campaigns(
        version.version_id,
        { after_id: cursor, limit: 20 },
        signal,
      ),
    [source.gateway, version.version_id, cursor],
  );
  const { state, query } = useGovernanceRead(load);
  const items = state.phase === "ready" ? state.value.items : [];
  const offer = items.find((row) => row.id === selected) ?? items[0] ?? null;
  return {
    state,
    query,
    cursor,
    selected,
    selectOffer: (id: string) => {
      setPacket(null);
      setSelected(id);
    },
    changePage: (value: string | number | null) => {
      query.clear();
      setSelected(null);
      setPacket(null);
      setCursor(value as string | null);
    },
    packet,
    setPacket,
    offer,
  };
}

function PublicPassportSection({
  source,
  version,
  offer,
  eligible,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
  offer: CampaignReceipt;
  eligible: boolean;
}) {
  return source.publications ? (
    <PassportPublication
      key={offer.id}
      gateway={source.publications}
      version={version}
      offer={offer}
      eligible={eligible}
    />
  ) : (
    <p>Public sharing is unavailable on this connection.</p>
  );
}
