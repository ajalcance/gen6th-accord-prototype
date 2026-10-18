import { useEffect, useRef, useState } from "react";
import Icon from "./icons";
import { SecurityReadiness } from "./console-footer";
import type { WorkspacePanelKind } from "./workspace-console";
import { useSavedSource } from "./saved-source";
import RuntimeReadinessPanel from "./runtime-readiness";
import BenchmarkReportPanel from "./benchmark-report";
import { workspacePages } from "./workspace-pages";

const TITLES = {
  guide: "Workspace guide",
  commands: "Quick actions",
  operations: "Connection & readiness",
};
const DESTINATIONS = workspacePages;

export default function WorkspacePanel(props: {
  kind: Exclude<WorkspacePanelKind, null>;
  close: () => void;
  navigate: (page: string) => void;
}) {
  const dialog = usePanelFocus(props.close, props.kind);
  return (
    <div className="drawer-overlay" onClick={props.close}>
      <div
        ref={dialog}
        className="console-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="workspace-panel-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="drawer-header">
          <h2 id="workspace-panel-title">{TITLES[props.kind]}</h2>
          <button
            className="icon-button"
            aria-label="Close panel"
            onClick={props.close}
          >
            <Icon name="close" />
          </button>
        </header>
        <div className="drawer-body">
          {props.kind === "guide" && <WorkspaceGuide />}
          {props.kind === "commands" && (
            <WorkspaceCommands navigate={props.navigate} />
          )}
          {props.kind === "operations" && <ConnectionReadiness />}
        </div>
      </div>
    </div>
  );
}

export function ConnectionReadiness({
  includeBenchmark = true,
}: {
  includeBenchmark?: boolean;
}) {
  const source = useSavedSource();
  return (
    <>
      <div className="connection-card">
        <span className={`status ${source ? "" : "warning"}`}>
          {source
            ? "Workspace connection configured"
            : "Persona API not connected"}
        </span>
        <h3>Connection status</h3>
        <p>
          Saved records require a trusted session. Each processing, evidence and
          passport capability has its own configuration and acceptance.
        </p>
      </div>
      <SecurityReadiness />
      {source?.runtime && <RuntimeReadinessPanel gateway={source.runtime} />}
      {includeBenchmark && <BenchmarkReportPanel />}
    </>
  );
}

function WorkspaceGuide() {
  return (
    <section>
      <p className="help">
        Use this guide to understand the record workflow and what each decision
        means.
      </p>
      <h3>System Capture</h3>
      <p>
        Choose the AI persona&apos;s face image and select Scan. A successfully
        scanned portrait, human contributions and AI disclosure are required to
        save a new registration before requesting independent review.
      </p>
      <h3>Review evidence and decisions</h3>
      <p>
        Inspect supplied evidence and missing permissions. A recorded review
        applies to its exact version; later edits require a new review.
      </p>
      <h3>Approve campaign use</h3>
      <p>
        Check the named parties, permitted assets, purpose and campaign window.
        A past acceptance does not override a revoked or expired permission.
      </p>
      <h3>Inspect a passport</h3>
      <p>
        Read the public claims and disclosures. Evidence presence, independent
        review and signature verification are separate states.
      </p>
      <h3>Frequently asked questions</h3>
      <details>
        <summary>What does a passport record?</summary>
        <p>
          A passport records claims, contributions, evidence and version-bound
          decisions. It does not establish legal ownership or worldwide
          originality. Signature verification is shown separately when
          available.
        </p>
      </details>
    </section>
  );
}

function WorkspaceCommands({ navigate }: { navigate: (page: string) => void }) {
  const [query, setQuery] = useState("");
  const matches = DESTINATIONS.filter((page) =>
    page.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <label className="search-field">
        <Icon name="search" />
        <input
          type="search"
          aria-label="Find a workspace page"
          value={query}
          maxLength={80}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Find a workspace page…"
        />
      </label>
      <div className="command-list">
        {matches.map((page) => (
          <button key={page} onClick={() => navigate(page)}>
            {page}
            <Icon name="arrow" />
          </button>
        ))}
      </div>
      {!matches.length && <p role="status">No matching workspace pages.</p>}
    </>
  );
}

function usePanelFocus(close: () => void, kind: string) {
  const dialog = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const trigger = document.activeElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const targets = () =>
      Array.from(
        dialog.current?.querySelectorAll<HTMLElement>(
          "button:not(:disabled), input:not(:disabled), summary, a[href]",
        ) ?? [],
      ).filter(
        (element) =>
          !element.closest("details:not([open])") ||
          element.tagName === "SUMMARY",
      );
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
      }
      if (event.key !== "Tab") return;
      const items = targets();
      if (event.shiftKey && document.activeElement === items[0]) {
        event.preventDefault();
        items.at(-1)?.focus();
      } else if (!event.shiftKey && document.activeElement === items.at(-1)) {
        event.preventDefault();
        items[0]?.focus();
      }
    };
    (
      dialog.current?.querySelector<HTMLElement>("input") ?? targets()[0]
    )?.focus();
    document.addEventListener("keydown", keyboard);
    return () => {
      document.body.style.overflow = overflow;
      document.removeEventListener("keydown", keyboard);
      if (trigger instanceof HTMLElement && trigger.isConnected)
        trigger.focus();
    };
  }, [close, kind]);
  return dialog;
}
