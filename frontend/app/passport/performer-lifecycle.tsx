import { useCallback, useState } from "react";
import type { LifecycleGateway } from "../../lib/persona-lifecycle";
import type {
  Dossier,
  LifecyclePage,
  LifecycleProfile,
  LifecycleReceipt,
} from "../../lib/persona-lifecycle-contracts";
import type { LifecycleFormProps } from "./lifecycle-form";
import type { RecordWorkspaceProps } from "./record-journey";
import { useGovernanceRead } from "./saved-governance-read";
import { GovernanceRead, RecordedTime } from "./governance-common";
import LifecycleDossier from "./lifecycle-dossier";
import LifecycleAssessments from "./lifecycle-assessments";
import LifecycleConcerns, { ConcernCard } from "./lifecycle-concerns";
import CopyReference from "./copy-reference";

export default function PerformerLifecycle(props: RecordWorkspaceProps) {
  const gateway = props.source.lifecycle;
  if (!gateway)
    return (
      <p role="status">
        Operator, rights and concern services are unavailable on this
        connection.
      </p>
    );
  if (gateway.workspaceId !== props.source.workspaceId)
    return <p role="alert">The lifecycle connection could not be validated.</p>;
  return (
    <LifecycleRecords
      key={`${props.source.sessionKey}:${props.version.version_id}`}
      {...props}
      gateway={gateway}
    />
  );
}
function LifecycleRecords(
  props: RecordWorkspaceProps & { gateway: LifecycleGateway },
) {
  const load = useCallback(
    (signal: AbortSignal) =>
      props.gateway.read(props.version.version_id, signal),
    [props.gateway, props.version.version_id],
  );
  const { state, query } = useGovernanceRead(load);
  const [historyOpen, setHistoryOpen] = useState(false);
  const form = { ...props, reload: () => void query.retry() };
  return (
    <section
      className="workflow-panel workflow-stack"
      aria-label="Rights and operator"
    >
      <h2>Rights &amp; operator</h2>
      <p className="help">
        Authority, rights and content have separate assessments. A new
        declaration needs fresh review before production clearance.
      </p>
      <GovernanceRead
        resource="Performer lifecycle"
        state={state}
        query={query}
      >
        {(profile) => <ProfileView {...form} profile={profile} />}
      </GovernanceRead>
      <details onToggle={(e) => setHistoryOpen(e.currentTarget.open)}>
        <summary>Inspect lifecycle history</summary>
        {historyOpen && <LifecycleHistory {...form} />}
      </details>
    </section>
  );
}
function ProfileView(form: LifecycleFormProps & { profile: LifecycleProfile }) {
  const { profile } = form;
  return (
    <>
      {profile.dossier?.content.kind === "dossier" ? (
        <DossierSummary
          receipt={profile.dossier}
          dossier={profile.dossier.content}
        />
      ) : (
        <p>No lifecycle declaration recorded for this version.</p>
      )}
      {form.source.writeGateway && (
        <LifecycleDossier
          key={profile.dossier?.id ?? "first"}
          {...form}
          previous={profile.dossier?.id ?? null}
          dossier={
            profile.dossier?.content.kind === "dossier"
              ? profile.dossier.content
              : null
          }
        />
      )}
      <LifecycleAssessments {...form} profile={profile} />
      <LifecycleConcerns {...form} profile={profile} />
    </>
  );
}
function DossierSummary({
  receipt,
  dossier,
}: {
  receipt: LifecycleReceipt;
  dossier: Dossier;
}) {
  return (
    <section
      className="workflow-stack"
      aria-label="Declared operator and rights"
    >
      <div className="governance-heading">
        <h3>{dossier.operator.name}</h3>
        <span className="status neutral">Owner declared</span>
      </div>
      <p>
        {dossier.operator.organization || "Individual operator"} · account{" "}
        {dossier.operator.actor_ref}
      </p>
      <p>{dossier.operator.authority}</p>
      <p className="help">
        Declared by {receipt.actor_ref} ·{" "}
        <RecordedTime value={receipt.recorded_at} />
      </p>
      <CopyReference label="Lifecycle declaration ID" value={receipt.id} />
      <p className="help">
        Authentication and declaration do not verify organization authority or
        ownership.
      </p>
      <DeclaredRights dossier={dossier} />
    </section>
  );
}
function DeclaredRights({ dossier }: { dossier: Dossier }) {
  return (
    <>
      {dossier.rights.map((right, i) => (
        <article key={i} className="governance-card">
          <h4>
            {right.kind.replaceAll("_", " ")} · {right.holder}
          </h4>
          <p>{right.scope}</p>
          <p>Withdrawal: {right.withdrawal}</p>
          <p className="help">
            <RecordedTime value={right.starts_at} /> →{" "}
            <RecordedTime value={right.ends_at} />
          </p>
        </article>
      ))}
      <details>
        <summary>Creation provenance · creator declared</summary>
        <p>
          {dossier.provenance.method.replaceAll("_", " ")} ·{" "}
          {dossier.provenance.provider} · {dossier.provenance.model_version}
        </p>
        <p>{dossier.provenance.disclosure}</p>
      </details>
    </>
  );
}
function LifecycleHistory(
  props: RecordWorkspaceProps & {
    gateway: LifecycleGateway;
    reload: () => void;
  },
) {
  const [cursor, setCursor] = useState<number | null>(null);
  const load = useCallback(
    (signal: AbortSignal) =>
      props.gateway.history(props.version.version_id, cursor, signal),
    [props.gateway, props.version.version_id, cursor],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <div className="workflow-stack">
      <GovernanceRead resource="Lifecycle history" state={state} query={query}>
        {(page) => (
          <HistoryRows
            {...props}
            page={page}
            reload={() => {
              void query.retry();
              props.reload();
            }}
          />
        )}
      </GovernanceRead>
      <HistoryControls
        cursor={cursor}
        loading={state.phase === "loading"}
        next={state.phase === "ready" ? state.value.next_before_ordinal : null}
        navigate={(value) => {
          query.clear();
          setCursor(value);
        }}
      />
    </div>
  );
}
function HistoryRows(props: LifecycleFormProps & { page: LifecyclePage }) {
  const { page } = props;
  return (
    <>
      {!page.items.length && <p>No lifecycle history on this page.</p>}
      {page.items.map((row) => (
        <article className="governance-card" key={row.id}>
          <h4>
            {row.content.kind} · receipt {row.ordinal}
          </h4>
          <p className="help">
            {row.actor_ref} · <RecordedTime value={row.recorded_at} />
          </p>
          {"statement" in row.content && <p>{row.content.statement}</p>}
          {row.content.kind === "concern" && (
            <HistoryConcern {...props} row={row} />
          )}
          <details>
            <summary>Receipt identifiers and evidence hashes</summary>
            <p>
              Version {row.version_id} · {row.id}
            </p>
            {Object.entries(row.evidence_digests).map(([id, hash]) => (
              <p key={id}>
                {id}: {hash}
              </p>
            ))}
          </details>
        </article>
      ))}
    </>
  );
}
function HistoryConcern(
  props: LifecycleFormProps & { page: LifecyclePage; row: LifecycleReceipt },
) {
  const entry = props.page.concerns.find(
    (entry) => entry.report.id === props.row.id,
  )!;
  return (
    <ConcernCard
      key={`${entry.report.id}:${entry.response?.id}`}
      {...props}
      entry={entry}
    />
  );
}
function HistoryControls({
  cursor,
  loading,
  next,
  navigate,
}: {
  cursor: number | null;
  loading: boolean;
  next: number | null;
  navigate: (value: number | null) => void;
}) {
  return (
    <div className="record-detail-actions">
      <button
        className="secondary"
        disabled={cursor === null || loading}
        onClick={() => navigate(null)}
      >
        Newest lifecycle records
      </button>
      <button
        className="secondary"
        disabled={next === null || loading}
        onClick={() => navigate(next)}
      >
        Older lifecycle records
      </button>
    </div>
  );
}
