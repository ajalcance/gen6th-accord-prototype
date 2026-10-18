import Icon from "./icons";
import { useSavedSource } from "./saved-source";

export default function ConsoleFooter(props: {
  setDrawer: (drawer: "operations") => void;
}) {
  const source = useSavedSource();
  return (
    <footer className="console-footer">
      <span className="footer-brand">ACCORD / PERSONA PASSPORT</span>
      <div className="footer-signals">
        <button
          className="footer-security"
          aria-label="Connection & capabilities"
          onClick={() => props.setDrawer("operations")}
        >
          <Icon name="shield" />
          <span>
            {source ? "Workspace session" : "Workspace disconnected"}{" "}
            <strong>Capabilities</strong>
          </span>
          <Icon name="arrow" />
        </button>
      </div>
    </footer>
  );
}

export function SecurityReadiness() {
  const source = useSavedSource();
  return (
    <section className="security-readiness" aria-label="Security readiness">
      <div className="panel-heading">
        <h3>Security readiness</h3>
        <Icon name="shield" />
      </div>
      <dl>
        <div>
          <dt>Workspace presence</dt>
          <dd>
            <span className="presence-light" aria-hidden="true" />
            Local UI active
          </dd>
        </div>
        <div>
          <dt>Trusted identity</dt>
          <dd>
            {source ? "Session checked on each request" : "Not connected"}
          </dd>
        </div>
        <div>
          <dt>Server security monitoring</dt>
          <dd>Not connected</dd>
        </div>
        <div>
          <dt>Runtime acceptance</dt>
          <dd>
            Check each capability below; configuration alone is not live
            acceptance.
          </dd>
        </div>
      </dl>
      <p className="help">
        The activity light describes this local interface only. No breach
        assessment, live threat feed or server health check is being performed.
      </p>
    </section>
  );
}
