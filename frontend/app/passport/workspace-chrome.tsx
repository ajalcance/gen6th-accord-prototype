import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import Icon from "./icons";
import { workspacePages, type WorkspacePage } from "./workspace-pages";

export type SessionAction = { label: string; run: () => void };
type SidebarProps = {
  page: WorkspacePage;
  navigate: (page: WorkspacePage) => void;
  collapsed: boolean;
  toggle: () => void;
  guide: () => void;
  label: string;
};
export function WorkspaceSidebar(props: SidebarProps) {
  return (
    <aside className={`sidebar ${props.collapsed ? "is-collapsed" : ""}`}>
      <SidebarBrand collapsed={props.collapsed} toggle={props.toggle} />
      <div className="workspace">
        <span className="workspace-icon">
          <Icon name="grid" size={18} />
        </span>
        <div>
          {props.label}
          <small>Persona Passport</small>
        </div>
      </div>
      <p className="nav-label">WORKSPACE</p>
      <JourneyLinks {...props} />
      <UtilityLinks {...props} />
    </aside>
  );
}
function SidebarBrand({
  collapsed,
  toggle,
}: Pick<SidebarProps, "collapsed" | "toggle">) {
  return (
    <div className="sidebar-brand-row">
      <Link className="wordmark" href="/" aria-label="Accord home">
        <Image
          unoptimized
          className="brand-mark"
          src="/brand/gen6th-icon.svg"
          width={28}
          height={28}
          alt=""
        />
        <span className="brand-name">Accord</span>
      </Link>
      <button
        className="sidebar-collapse icon-button"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        aria-expanded={!collapsed}
        aria-controls="journey-navigation"
        onClick={toggle}
      >
        <Icon name="menu" />
      </button>
    </div>
  );
}
function JourneyLinks(props: Pick<SidebarProps, "page" | "navigate">) {
  return (
    <nav id="journey-navigation" aria-label="Persona journey">
      {workspacePages
        .filter((page) => page !== "Settings")
        .map((page, index) => (
          <button
            key={page}
            className={`nav-item ${props.page === page ? "active" : ""}`}
            aria-label={page}
            title={page}
            aria-current={props.page === page ? "page" : undefined}
            onClick={() => props.navigate(page)}
          >
            <Icon
              name={
                (["grid", "create", "scan", "shield", "passport"] as const)[
                  index
                ]
              }
            />
            <span className="nav-text">{page}</span>
          </button>
        ))}
    </nav>
  );
}
function UtilityLinks(
  props: Pick<SidebarProps, "page" | "navigate" | "guide">,
) {
  return (
    <nav className="workspace-utilities" aria-label="Workspace utilities">
      <button
        className={`nav-item ${props.page === "Settings" ? "active" : ""}`}
        aria-label="Settings"
        title="Settings"
        aria-current={props.page === "Settings" ? "page" : undefined}
        onClick={() => props.navigate("Settings")}
      >
        <Icon name="settings" />
        <span className="nav-text">Settings</span>
      </button>
      <button
        className="nav-item"
        aria-label="Help & guide"
        title="Help & guide"
        onClick={props.guide}
      >
        <Icon name="file" />
        <span className="nav-text">Help &amp; guide</span>
      </button>
    </nav>
  );
}
export function WorkspaceHeader({
  page,
  commands,
  sessionAction,
}: {
  page: WorkspacePage;
  commands: () => void;
  sessionAction?: SessionAction;
}) {
  return (
    <header className="topbar">
      <div className="breadcrumb">
        Persona Passport <span>/</span> {page}
      </div>
      <div
        className="workspace-actions"
        role="group"
        aria-label="Workspace actions"
      >
        <button
          className="secondary compact"
          aria-label="Quick actions"
          title="Quick actions (⌘ / Ctrl K)"
          onClick={commands}
        >
          <Icon name="command" size={16} />
          <span className="action-label">Actions</span>
          <kbd className="action-shortcut">⌘ K</kbd>
        </button>
        {sessionAction && <AccountControl action={sessionAction} />}
      </div>
    </header>
  );
}
function AccountControl({ action }: { action: SessionAction }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="account-control"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setOpen(false);
          event.currentTarget.querySelector("button")?.focus();
        }
      }}
    >
      <button
        className="secondary compact"
        aria-expanded={open}
        aria-controls="account-actions"
        onClick={() => setOpen(!open)}
      >
        Account
      </button>
      {open && (
        <div id="account-actions" className="account-actions">
          <button className="secondary" onClick={action.run}>
            {action.label}
          </button>
        </div>
      )}
    </div>
  );
}
