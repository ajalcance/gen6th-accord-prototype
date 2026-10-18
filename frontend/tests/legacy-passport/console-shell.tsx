import Link from "next/link";
import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";

export const STEPS = [
  "Records",
  "System Capture",
  "Analysis & review",
  "Campaign approval",
  "Public passport",
];
const HEADLINES = [
  "Records",
  "System Capture record",
  "Analysis workspace",
  "Campaign approval",
  "Passport preview",
];
const SUBTITLES = [
  "Browse browser fixtures or inspect saved workspace records.",
  "Document the character, human contribution and AI disclosure.",
  "Inspect references and evidence gaps before independent review.",
  "Review the exact version, named parties and permitted scope.",
  "Inspect the public projection, disclosures and verification state.",
];

function SidebarCollapse(props: StudioState) {
  const label = props.sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar";
  return (
    <button
      className="sidebar-collapse icon-button"
      aria-label={label}
      title={label}
      aria-expanded={!props.sidebarCollapsed}
      aria-controls="journey-navigation"
      onClick={() =>
        props.dispatch({ type: "sidebar", value: !props.sidebarCollapsed })
      }
    >
      <Icon name="menu" />
    </button>
  );
}

function SidebarBrand(props: StudioState) {
  return (
    <div className="sidebar-brand-row">
      <Link className="wordmark" href="/" aria-label="Accord home">
        <span className="brand-icon">a</span>
        <span className="brand-name">accord</span>
      </Link>
      <SidebarCollapse {...props} />
    </div>
  );
}

export function JourneySidebar(props: StudioState) {
  const icons = ["grid", "create", "scan", "shield", "passport"] as const;
  return (
    <aside
      className={`sidebar ${props.sidebarCollapsed ? "is-collapsed" : ""}`}
    >
      <SidebarBrand {...props} />
      <div className="workspace">
        <span className="workspace-icon">N</span>
        <div>
          North Studio<small>Fictional workspace</small>
        </div>
      </div>
      <p className="nav-label">WORKSPACE</p>
      <nav id="journey-navigation" aria-label="Persona journey">
        {STEPS.map((label, index) => (
          <button
            key={label}
            aria-label={label}
            title={label}
            className={`nav-item ${props.step === index ? "active" : ""}`}
            onClick={() => props.setStep(index)}
            aria-current={props.step === index ? "step" : undefined}
          >
            <Icon name={icons[index]} />
            <span className="nav-text">{label}</span>
            {index === 0 && (
              <span className="count">{props.records.length}</span>
            )}
          </button>
        ))}
      </nav>
      <SidebarUtilities {...props} />
    </aside>
  );
}

export function ConsoleHeader(props: StudioState) {
  return (
    <>
      <header className="topbar">
        <div className="breadcrumb">
          <span className="breadcrumb-product">Persona Passport</span>
          <span>/</span>
          {STEPS[props.step]}
          {props.step !== 0 && (
            <small>
              {props.draft.name || "Untitled fixture"} · v{props.revision}
            </small>
          )}
        </div>
        <div className="header-actions">
          <button
            className="command-trigger"
            aria-label="Quick actions"
            title="Search screens, personas and tools"
            onClick={() => props.setDrawer("commands")}
          >
            <Icon name="search" />
            <span>Quick actions</span>
            <kbd>⌘ / Ctrl K</kbd>
          </button>
          <button
            className="secondary compact"
            onClick={() => props.setDrawer("assistant")}
          >
            <Icon name="spark" />
            <span>Demo guide</span>
          </button>
          <span className="avatar" aria-label="Fictional North Studio">
            NS
          </span>
        </div>
      </header>
      <details className="demo-banner">
        <summary>Fictional demo · browser-only · unsigned</summary>
        <p>
          Use fictional inputs only. No AI analysis, identity checks or
          signatures. Browser-only preview; no persona records are sent to the
          backend.
        </p>
      </details>
    </>
  );
}

export function JourneyHeading(props: StudioState & { saved?: boolean }) {
  return (
    <div className="page-heading">
      <div>
        <h1 tabIndex={-1}>{HEADLINES[props.step]}</h1>
        <p className="subtitle">{SUBTITLES[props.step]}</p>
      </div>
      {props.step === 0 ? (
        props.saved ? null : (
          <button
            className="primary"
            disabled={props.records.length >= 12}
            onClick={props.createPersona}
          >
            <Icon name="create" />
            Start System Capture
          </button>
        )
      ) : (
        <button
          className="record-trigger secondary"
          onClick={() => props.setDrawer("records")}
        >
          <Icon name="history" />
          <span>
            {props.draft.name || "Untitled fixture"}
            <small>
              fixture-v{props.revision}
              {props.dirty ? " · draft edited" : " · local only"}
            </small>
          </span>
        </button>
      )}
    </div>
  );
}

function SidebarUtilities(props: StudioState) {
  return (
    <>
      <p className="nav-label section-label">INSIGHT & RECORDS</p>
      <div className="utility-nav">
        <button
          aria-label="Evidence & decisions"
          title="Evidence & decisions"
          onClick={() => props.setDrawer("governance")}
        >
          <Icon name="shield" />
          <span className="nav-text">Evidence & decisions</span>
        </button>
        <button
          aria-label="Activity & versions"
          title="Activity & versions"
          onClick={() => props.setDrawer("records")}
        >
          <Icon name="history" />
          <span className="nav-text">Activity & versions</span>
        </button>
        <button
          aria-label="Connection & readiness"
          title="Connection & readiness"
          onClick={() => props.setDrawer("operations")}
        >
          <Icon name="pulse" />
          <span className="nav-text">Connection & readiness</span>
        </button>
      </div>
      <div className="sidebar-bottom">
        <span className="demo-dot" />
        Local fixture workspace
        <button
          className="sidebar-connection"
          onClick={() => props.setDrawer("operations")}
        >
          Connection details <Icon name="arrow" />
        </button>
      </div>
    </>
  );
}
