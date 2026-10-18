import Portrait from "./portrait";
import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";
import { campaignBlocks } from "./console-fixtures";
import { isDraftReady } from "./fixture-data";
import { publicFixture } from "./console-storage";

export default function PublicPassport(props: StudioState) {
  return (
    <div className="public-layout">
      <PassportCover {...props} />
      <PublicProjection {...props} />
    </div>
  );
}
function PassportCover(props: StudioState) {
  return (
    <section className="passport-cover">
      <div className="passport-art">
        <Portrait variant={props.variant} />
        <span className="passport-mark">a / ACCORD</span>
        <span className="portrait-tag">FICTIONAL / UNISSUED</span>
      </div>
      <div className="passport-cover-copy">
        <p className="eyebrow">PERSONA PASSPORT / LOCAL PREVIEW</p>
        <h2>{props.committed.name || "Unissued fictional draft"}</h2>
        <p>
          {props.committed.bio ||
            "Complete the System Capture record before exporting this preview."}
        </p>
        <div className="passport-id">
          <span>
            fixture:{props.id}:v{props.revision}
          </span>
          <span className="status">Unsigned design preview</span>
        </div>
      </div>
    </section>
  );
}
function PublicProjection(props: StudioState) {
  return (
    <section className="panel public-projection">
      <div className="section-bar">
        <p className="eyebrow">PUBLIC PROJECTION / LOCAL PREVIEW</p>
        <div className="segmented-control" aria-label="Preview audience">
          <button
            aria-pressed={props.publicView}
            onClick={() => props.setPublicView(true)}
          >
            Public preview
          </button>
          <button
            aria-pressed={!props.publicView}
            onClick={() => props.setPublicView(false)}
          >
            Private preview
          </button>
        </div>
      </div>
      <h2>Provenance & decisions</h2>
      <p className="help">
        {props.publicView
          ? "Public fixture fields only. Private notes are excluded from the download."
          : "Private preview — fictional workspace notes. No access-control boundary is implemented."}
      </p>
      <PassportTimeline {...props} />
      {!props.publicView && (
        <div className="private-note">
          <strong>Private reviewer note</strong>
          <p>{props.comment || "No reviewer comment yet."}</p>
        </div>
      )}
      <div className="disclosure-block">
        <p className="eyebrow">AI DISCLOSURE</p>
        <p>{props.committed.disclosure || "No disclosure supplied."}</p>
      </div>
      <PassportVerification />
      <PassportExport {...props} />
      <p className="help">
        Sharing, QR issuance and real public publication remain unavailable.
        This preview does not establish copyright, identity or worldwide
        originality.
      </p>
    </section>
  );
}
function PassportTimeline(props: StudioState) {
  const blocked = campaignBlocks(props.record).length > 0;
  return (
    <ol className="timeline passport-timeline">
      <li>
        <strong>Created by North Studio</strong>
        <p>Fictional character record · fixture-v{props.revision}</p>
      </li>
      <li>
        <strong>
          {props.reviewed ? "Demo review recorded" : "Review pending"}
        </strong>
        <p>Independent human scenario; no server receipt.</p>
      </li>
      <li>
        <strong>
          {props.revoked
            ? "Demo offer revoked"
            : props.withdrawn
              ? "Campaign changes requested"
              : props.approved
                ? "Campaign scope accepted in demo"
                : "Campaign acceptance pending"}
        </strong>
        <p>
          A quieter kind of summer ·{" "}
          {blocked
            ? "current fixture use blocked"
            : "eligible in simulated window"}
          .
        </p>
      </li>
    </ol>
  );
}
function PassportVerification() {
  return (
    <>
      <div className="verification">
        <Icon name="shield" size={25} />
        <div>
          <strong>No signature issued</strong>
          <p>
            A platform-issued manifest and trusted key are required. This
            unsigned fixture cannot prove ownership or integrity.
          </p>
        </div>
      </div>
      <details className="verification-requirements">
        <summary>What is required for verification?</summary>
        <p className="help">
          Unsigned fixture — verification unavailable. A platform-issued
          manifest, signature and trusted key are required. No platform key or
          signed manifest exists.
        </p>
      </details>
    </>
  );
}

function PassportExport(props: StudioState) {
  return (
    <section className="passport-export" aria-label="Unsigned export">
      <details className="export-preview">
        <summary>Review export fields</summary>
        <p className="help">
          Committed public fields only. Private reviewer notes are excluded.
        </p>
        <pre>{JSON.stringify(publicFixture(props.record), null, 2)}</pre>
      </details>
      <button
        className="primary"
        disabled={!isDraftReady(props.committed)}
        onClick={props.download}
      >
        Download unsigned JSON <Icon name="arrow" />
      </button>
      {!isDraftReady(props.committed) && (
        <p className="help">
          Complete and save the System Capture record before downloading.
        </p>
      )}
    </section>
  );
}
