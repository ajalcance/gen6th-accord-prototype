import { useCallback } from "react";
import type { SavedPersonaSource } from "./saved-source";
import type { WriteDraftState } from "./prepared-write-common";
import { useGovernanceRead } from "./saved-governance-read";
import { GovernanceRead } from "./governance-common";
import type { LifecycleGateway } from "../../lib/persona-lifecycle";
import type { LifecycleProfile } from "../../lib/persona-lifecycle-contracts";

type Props = {
  source: SavedPersonaSource;
  versionId: string;
  draft: WriteDraftState;
};
export default function LifecycleUse(props: Props) {
  if (!props.source.lifecycle)
    return (
      <p className="help">
        Operator and rights binding is unavailable on this connection.
      </p>
    );
  if (props.source.lifecycle.workspaceId !== props.source.workspaceId)
    return <p role="alert">The lifecycle connection could not be validated.</p>;
  return (
    <fieldset>
      <legend>Reviewed authority &amp; rights</legend>
      <label className="prepared-confirm">
        <input
          type="checkbox"
          checked={props.draft.fields.lifecycle === "yes"}
          onChange={(e) =>
            props.draft.change("lifecycle", e.target.checked ? "yes" : "")
          }
        />
        Bind reviewed authority and rights to this use
      </label>
      {props.draft.fields.lifecycle === "yes" && (
        <UseBinding {...props} gateway={props.source.lifecycle} />
      )}
    </fieldset>
  );
}
function UseBinding(props: Props & { gateway: LifecycleGateway }) {
  const load = useCallback(
    (signal: AbortSignal) => props.gateway.read(props.versionId, signal),
    [props.gateway, props.versionId],
  );
  const { state, query } = useGovernanceRead(load),
    { draft } = props;
  return (
    <>
      <GovernanceRead
        resource="Reviewed authority and rights"
        state={state}
        query={query}
      >
        {(profile) => <ReviewedBinding profile={profile} draft={draft} />}
      </GovernanceRead>
      <UseOptions draft={draft} />
    </>
  );
}
function ReviewedBinding({
  profile,
  draft,
}: {
  profile: LifecycleProfile;
  draft: WriteDraftState;
}) {
  const dossier = profile.dossier;
  if (!dossier || dossier.content.kind !== "dossier")
    return <p>Record a declaration in Rights &amp; operator first.</p>;
  const operator = dossier.content.operator;
  const ready =
    !profile.suspended &&
    profile.requirements.every((item) => item.status === "approved");
  return (
    <>
      <p>
        {operator.name} ·{" "}
        {profile.requirements
          .map((r) => `${r.requirement}: ${r.status}`)
          .join(" · ")}
      </p>
      <button
        type="button"
        className="secondary"
        disabled={!ready}
        onClick={() =>
          draft.changeFields({
            lifecycleProfile: dossier.id,
            lifecycleOperator: operator.actor_ref,
          })
        }
      >
        Use this reviewed declaration
      </button>
      {draft.fields.lifecycleProfile === dossier.id && (
        <p role="status">
          Declaration selected. The server rechecks it when recording and
          accepting the offer.
        </p>
      )}
      {!ready && (
        <p>
          Complete independent assessments and resolve any suspension before
          clearance.
        </p>
      )}
    </>
  );
}
function UseOptions({ draft }: { draft: WriteDraftState }) {
  return (
    <>
      <UseMode draft={draft} />
      <label className="prepared-confirm">
        <input
          type="checkbox"
          checked={draft.fields.voiceUse === "yes"}
          onChange={(e) =>
            draft.change("voiceUse", e.target.checked ? "yes" : "")
          }
        />
        Include voice use · requires voice rights
      </label>
      <p className="help">
        The permission window must fit every applicable right and assessment. A
        new role, distribution or declaration needs a new offer.
      </p>
    </>
  );
}
function UseMode({ draft }: { draft: WriteDraftState }) {
  return (
    <>
      <label>
        Use mode
        <select
          value={draft.fields.useMode || "production"}
          onChange={(e) =>
            draft.changeFields({
              useMode: e.target.value,
              ...(e.target.value === "trial"
                ? { distribution: "private" }
                : {}),
            })
          }
        >
          <option value="production">Production</option>
          <option value="trial">Private trial · up to 30 days</option>
        </select>
      </label>
      <label>
        Distribution
        <select
          value={
            draft.fields.useMode === "trial"
              ? "private"
              : draft.fields.distribution || "public"
          }
          disabled={draft.fields.useMode === "trial"}
          onChange={(e) => draft.change("distribution", e.target.value)}
        >
          <option value="private">Private</option>
          <option value="public">Public</option>
        </select>
      </label>
    </>
  );
}
