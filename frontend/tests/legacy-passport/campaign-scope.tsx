import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";
import { scopeIsValid } from "./console-fixtures";

export default function CampaignScope(props: StudioState) {
  return (
    <section className="panel scope-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">03 / CAMPAIGN AUTHORIZATION</p>
          <h2>Campaign scope</h2>
          <p className="help">
            A quieter kind of summer · North Studio × Solstice Goods · fictional
            parties
          </p>
        </div>
        <Icon name="shield" size={26} />
      </div>
      <dl className="details">
        <dt>Exact persona version</dt>
        <dd>
          {props.committed.name || "Incomplete fictional draft"} / fixture-v
          {props.revision}
        </dd>
        <dt>Named recipient</dt>
        <dd>Solstice Goods · fictional brand</dd>
        <dt>Asset binding</dt>
        <dd>
          Canonical vector portrait · palette {props.variant + 1}
          <small>
            Fixture reference only; no uploaded bytes or verified digest
          </small>
        </dd>
      </dl>
      <ScopeFields {...props} />
      <p className="scope-state" role="status">
        {props.revoked
          ? "Revoked offer · a new offer is required"
          : props.withdrawn
            ? "Changes requested · a new scope is required"
            : props.offered
              ? "Current demo offer · scope bound to this version"
              : "Editable scope · no current offer"}
      </p>
      <ScopeOffer {...props} />
    </section>
  );
}
function ScopeFields(props: StudioState) {
  const disabled = props.campaignActor !== "creator";
  return (
    <div className="scope-fields">
      <label>
        Campaign purpose
        <textarea
          aria-label="Campaign purpose"
          disabled={disabled}
          maxLength={500}
          value={props.scope.purpose}
          onChange={(event) => props.setScope("purpose", event.target.value)}
        />
      </label>
      <div className="date-fields">
        <label>
          Starts on
          <input
            type="date"
            aria-label="Campaign starts on"
            disabled={disabled}
            value={props.scope.startsAt}
            onChange={(event) => props.setScope("startsAt", event.target.value)}
          />
        </label>
        <label>
          Ends on
          <input
            type="date"
            aria-label="Campaign ends on"
            disabled={disabled}
            value={props.scope.endsAt}
            onChange={(event) => props.setScope("endsAt", event.target.value)}
          />
        </label>
      </div>
      <p className="help">UTC calendar dates · maximum 366 days</p>
      <label>
        Conditions
        <textarea
          aria-label="Campaign conditions"
          disabled={disabled}
          maxLength={500}
          value={props.scope.conditions}
          onChange={(event) => props.setScope("conditions", event.target.value)}
        />
      </label>
    </div>
  );
}

function ScopeOffer(props: StudioState) {
  const editable = props.campaignActor === "creator";
  return (
    <div className="scope-footer">
      <p className="help">
        An offer belongs to this exact version and scope. Editing scope requires
        a new owner offer.
      </p>
      <button
        className="primary"
        disabled={
          !editable ||
          !props.reviewed ||
          props.dirty ||
          !scopeIsValid(props.scope) ||
          props.window === "expired"
        }
        onClick={() => props.dispatch({ type: "offer" })}
      >
        <Icon name="file" />
        {props.offered ? "Issue replacement demo offer" : "Create demo offer"}
      </button>
      <OfferBlockers {...props} />
    </div>
  );
}

function OfferBlockers(props: StudioState) {
  const editable = props.campaignActor === "creator";
  return (
    <>
      {!props.reviewed && (
        <p role="status" className="help">
          Complete the demo review before issuing or accepting this scope.
        </p>
      )}
      {!scopeIsValid(props.scope) && (
        <p role="status" className="warning-text">
          Supply purpose/conditions and a positive duration of at most 366 days.
        </p>
      )}
      {props.dirty && (
        <p className="help">
          Save the changed persona version and complete a new review first.
        </p>
      )}
      {props.window === "expired" && (
        <p className="help">
          The simulated window has expired. Adjust Demo controls to explore a
          new offer.
        </p>
      )}
      {!editable && (
        <p className="help">
          Only the fictional creator can edit or offer this scope. Use Demo
          controls to change parties.
        </p>
      )}
    </>
  );
}
