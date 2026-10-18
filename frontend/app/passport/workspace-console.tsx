"use client";

import { useEffect, useRef, useState } from "react";
import SavedGallery from "./saved-gallery";
import SavedRecord from "./saved-record";
import { useSavedSource } from "./saved-source";
import ConsoleFooter from "./console-footer";
import WorkspacePanel from "./workspace-panel";
import RecordCreation from "./record-creation";
import WorkspaceSettings from "./workspace-settings";
import PersonaPicker from "./persona-picker";
import useWorkspaceControls from "./use-workspace-controls";
import {
  WorkspaceHeader,
  WorkspaceSidebar,
  type SessionAction,
} from "./workspace-chrome";
import {
  workspacePages,
  journeyEntries,
  type JourneyPage,
  type WorkspacePage,
  type RecordNavigation,
} from "./workspace-pages";

export type WorkspacePanelKind = "guide" | "commands" | "operations" | null;

export default function WorkspaceConsole({
  sessionAction,
}: {
  sessionAction?: SessionAction;
}) {
  const source = useSavedSource();
  const owner = source
    ? `${source.workspaceId}:${source.sessionKey}`
    : "unconnected";
  const controls = useWorkspaceControls(owner);
  const [view, setView] = useState<"grid" | "list">("grid");
  const navigation = {
    open: controls.openRecord,
    navigate: controls.navigate,
    version: controls.version,
    loaded: controls.loaded,
  };
  return (
    <div className="console-root workspace-console">
      <a
        href="#workspace-main"
        className="skip-link"
        inert={controls.panel !== null}
      >
        Skip to workspace
      </a>
      <WorkspaceShell
        controls={controls}
        view={view}
        setView={setView}
        navigation={navigation}
        label={source?.workspaceLabel ?? "Workspace"}
        sessionAction={sessionAction}
      />
      {controls.panel && (
        <WorkspacePanel
          kind={controls.panel}
          close={controls.close}
          navigate={(next) => {
            if (workspacePages.includes(next as WorkspacePage))
              controls.navigate(next as WorkspacePage);
            controls.close();
          }}
        />
      )}
    </div>
  );
}

type Controls = ReturnType<typeof useWorkspaceControls>;
function WorkspaceMain({
  controls,
  view,
  setView,
  navigation,
  signIn,
}: {
  controls: Controls;
  view: "grid" | "list";
  setView: (view: "grid" | "list") => void;
  navigation: RecordNavigation;
  signIn?: () => void;
}) {
  const main = useRef<HTMLElement>(null);
  const previous = useRef(controls.page);
  useEffect(() => {
    if (previous.current !== controls.page)
      main.current
        ?.querySelector<HTMLElement>("[data-active-page] h1")
        ?.focus();
    previous.current = controls.page;
  }, [controls.page]);
  return (
    <main id="workspace-main" ref={main}>
      <div
        hidden={controls.page !== "Records"}
        data-active-page={controls.page === "Records" ? "" : undefined}
      >
        <SavedGallery
          active={controls.page === "Records"}
          target={controls.showRecord ? controls.target : null}
          navigation={navigation}
          closeRecord={() => controls.navigate("Records")}
          create={() => controls.navigate("System Capture")}
          signIn={signIn}
          view={view}
          setView={setView}
        />
      </div>
      <div data-active-page={controls.page !== "Records" ? "" : undefined}>
        {controls.page === "System Capture" && (
          <RecordCreation
            records={() => controls.navigate("Records")}
            open={controls.openRecord}
            prepare={(id) => controls.openRecord(id, "References")}
          />
        )}
        {controls.page === "Settings" && (
          <WorkspaceSettings view={view} setView={setView} />
        )}
        {["Analysis & review", "Production & use", "Passports"].includes(
          controls.page,
        ) && <JourneyWorkspace controls={controls} navigation={navigation} />}
      </div>
    </main>
  );
}

function JourneyWorkspace({
  controls,
  navigation,
}: {
  controls: Controls;
  navigation: RecordNavigation;
}) {
  const source = useSavedSource();
  if (!source || source.gateway.workspaceId !== source.workspaceId)
    return (
      <section>
        <h1 tabIndex={-1}>{controls.page}</h1>
        <p role="status">Sign in to choose a saved performer.</p>
      </section>
    );
  if (!controls.target)
    return (
      <section className="journey-entry">
        <h1 tabIndex={-1}>{controls.page}</h1>
        <p className="journey-introduction">
          {journeyEntries[controls.page as JourneyPage].description}
        </p>
        <PersonaPicker
          key={`${source.workspaceId}:${source.sessionKey}`}
          source={source}
          select={controls.choose}
          journey={controls.page as JourneyPage}
        />
      </section>
    );
  return (
    <SavedRecord
      key={`${source.workspaceId}:${source.sessionKey}:${controls.target.id}:${controls.target.revision}`}
      source={source}
      personaId={controls.target.id}
      revision={controls.target.revision}
      journey={
        controls.page as "Analysis & review" | "Production & use" | "Passports"
      }
      navigation={navigation}
      close={controls.clearSelection}
    />
  );
}

function WorkspaceShell({
  controls,
  view,
  setView,
  navigation,
  label,
  sessionAction,
}: {
  controls: Controls;
  view: "grid" | "list";
  setView: (view: "grid" | "list") => void;
  navigation: RecordNavigation;
  label: string;
  sessionAction?: SessionAction;
}) {
  return (
    <div className="studio" inert={controls.panel !== null}>
      <WorkspaceSidebar
        page={controls.page}
        navigate={controls.navigate}
        collapsed={controls.collapsed}
        toggle={() => controls.setCollapsed(!controls.collapsed)}
        guide={() => controls.setPanel("guide")}
        label={label}
      />
      <div className="main-shell">
        <WorkspaceHeader
          page={controls.page}
          sessionAction={sessionAction}
          commands={() => controls.setPanel("commands")}
        />
        <WorkspaceMain
          controls={controls}
          view={view}
          setView={setView}
          navigation={navigation}
          signIn={
            sessionAction?.label === "Sign in" ? sessionAction.run : undefined
          }
        />
        <ConsoleFooter setDrawer={() => controls.navigate("Settings")} />
      </div>
    </div>
  );
}
