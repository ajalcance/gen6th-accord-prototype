import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";
import { canAccept, campaignBlocks } from "./console-fixtures";
import { CampaignDemoControls, RevokeOffer } from "./campaign-controls";

export function CampaignActor(props: StudioState) {
  return (
    <div className="campaign-actor-bar">
      <div>
        <span className="eyebrow">DEMO PARTY CONTEXT</span>
        <strong>
          {props.campaignActor === "creator"
            ? "North Studio · owner offer"
            : "Solstice Goods · named recipient"}
        </strong>
        <small>Scenario controls, not trusted sessions</small>
      </div>
      <CampaignDemoControls {...props} />
    </div>
  );
}
export function RecipientDecision(props: StudioState) {
  return (
    <section className="panel recipient-panel">
      <div className="panel-heading">
        <h3>Recipient decision</h3>
        <span className="status">Human scenario</span>
      </div>
      <p className="help">
        The named recipient accepts or requests changes. The creator can revoke;
        neither action establishes legal title.
      </p>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={props.confirmed}
          disabled={
            !props.offered ||
            props.revoked ||
            props.withdrawn ||
            props.campaignActor !== "recipient"
          }
          onChange={(event) => props.setConfirmed(event.target.checked)}
        />
        I have read this fictional scope and want to simulate acceptance.
      </label>
      <RecipientActions {...props} />
      {props.campaignActor !== "recipient" && (
        <p className="help">
          Switch to the named recipient in Demo controls to accept or request
          changes.
        </p>
      )}
      {!props.offered && (
        <p role="status" className="help">
          The fictional creator must issue a current offer first.
        </p>
      )}
    </section>
  );
}
export function PermissionStatus(props: StudioState) {
  const reasons = campaignBlocks(props.record);
  return (
    <section
      className={`permission-status ${reasons.length ? "blocked" : "eligible"}`}
    >
      <div className="panel-heading">
        <Icon name="shield" size={26} />
        <span className={`status ${reasons.length ? "warning" : "success"}`}>
          {reasons.length ? "Fixture use blocked" : "Eligible in this fixture"}
        </span>
      </div>
      <h3>
        {props.revoked
          ? "Offer revoked"
          : props.withdrawn
            ? "A new scope is needed"
            : props.approved
              ? "Accepted. Check current use."
              : "Specific use. Visible conditions."}
      </h3>
      <ul className="block-list">
        {reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
      {!reasons.length && (
        <p>
          No fixture blockers remain. This is not a live permission grant or
          signed record.
        </p>
      )}
      <button className="text-button" onClick={() => props.ask("scope")}>
        <Icon name="spark" />
        Explain permission state
      </button>
      {!props.reviewed && (
        <button className="text-button" onClick={() => props.setStep(2)}>
          Resolve review requirement <Icon name="arrow" />
        </button>
      )}
    </section>
  );
}
function RecipientActions(props: StudioState) {
  return (
    <>
      <div className="button-row">
        <button
          className="secondary"
          disabled={
            !props.offered ||
            props.revoked ||
            props.campaignActor !== "recipient"
          }
          onClick={() => props.dispatch({ type: "campaignChanges" })}
        >
          Request changes
        </button>
        {!props.approved ? (
          <button
            className="primary"
            disabled={!canAccept(props.record)}
            onClick={() => {
              if (props.acceptScope()) props.setStep(4);
            }}
          >
            Accept demo scope
            <Icon name="arrow" />
          </button>
        ) : (
          <p role="status" className="accepted-notice">
            Scope accepted in this demo. Current eligibility is shown
            separately.
          </p>
        )}
      </div>
      <RevokeOffer
        key={`${props.id}:${props.revision}:${props.history.at(-1)?.id}:${props.campaignActor}`}
        {...props}
      />
    </>
  );
}
