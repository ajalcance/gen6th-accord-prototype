import { useState } from "react";
import type { StudioState } from "./use-studio";

export function RevokeOffer(props: StudioState) {
  const [confirming, setConfirming] = useState(false);
  if (!props.offered || props.revoked || props.campaignActor !== "creator")
    return null;
  return (
    <section className="owner-actions" aria-label="Owner actions">
      <h3>Owner actions</h3>
      {!confirming ? (
        <button
          className="text-button danger-text"
          onClick={() => setConfirming(true)}
        >
          Revoke demo offer
        </button>
      ) : (
        <div className="revoke-confirmation">
          <strong>Revoke this offer?</strong>
          <p>
            {props.committed.name} · fixture-v{props.revision} · Solstice Goods
          </p>
          <p className="help">
            {props.scope.purpose} · {props.scope.startsAt}–{props.scope.endsAt}.
            Acceptance will be withdrawn. This offer cannot be accepted again; a
            new offer is required.
          </p>
          <div className="button-row">
            <button className="secondary" onClick={() => setConfirming(false)}>
              Keep offer
            </button>
            <button
              className="destructive"
              onClick={() => {
                props.dispatch({ type: "revoke" });
                setConfirming(false);
              }}
            >
              Confirm revocation
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

export function CampaignDemoControls(props: StudioState) {
  return (
    <details className="demo-controls">
      <summary>Demo controls · fictional party and time</summary>
      <div className="segmented-control" aria-label="Demo campaign party">
        <button
          aria-pressed={props.campaignActor === "creator"}
          onClick={() =>
            props.dispatch({ type: "campaignActor", actor: "creator" })
          }
        >
          Act as creator
        </button>
        <button
          aria-pressed={props.campaignActor === "recipient"}
          onClick={() =>
            props.dispatch({ type: "campaignActor", actor: "recipient" })
          }
        >
          Act as recipient
        </button>
      </div>
      <label>
        Simulated campaign window
        <select
          value={props.window}
          onChange={(event) =>
            props.dispatch({
              type: "window",
              value:
                event.target.value === "active"
                  ? "active"
                  : event.target.value === "expired"
                    ? "expired"
                    : "before",
            })
          }
        >
          <option value="before">Before campaign starts</option>
          <option value="active">Inside campaign window</option>
          <option value="expired">After campaign expires</option>
        </select>
      </label>
      <p className="help">
        Scenario controls only. Live roles and eligibility require trusted
        sessions and server time.
      </p>
    </details>
  );
}
