import { useState } from "react";
import { ConnectionReadiness } from "./workspace-panel";
import BenchmarkReportPanel from "./benchmark-report";
import GalleryDisplay from "./gallery-display";

export default function WorkspaceSettings({
  view,
  setView,
}: {
  view: "grid" | "list";
  setView: (view: "grid" | "list") => void;
}) {
  const [section, setSection] = useState("Connection & capabilities");
  return (
    <section className="workspace-settings" aria-label="Workspace settings">
      <h1 tabIndex={-1}>Settings</h1>
      <p className="help">Workspace preferences and capability status.</p>
      <div
        className="workspace-tabs"
        role="group"
        aria-label="Settings sections"
      >
        {[
          "Connection & capabilities",
          "Recognition evidence",
          "Preferences",
        ].map((item) => (
          <button
            className="secondary"
            key={item}
            aria-pressed={section === item}
            onClick={() => setSection(item)}
          >
            {item}
          </button>
        ))}
      </div>
      <div className="settings-content">
        {section === "Connection & capabilities" && (
          <ConnectionReadiness includeBenchmark={false} />
        )}
        {section === "Recognition evidence" && <BenchmarkReportPanel />}
        {section === "Preferences" && (
          <section className="settings-preferences">
            <h2>Record presentation</h2>
            <GalleryDisplay view={view} setView={setView} />
            <p className="help">
              Applies to this browser tab. Account settings are not changed.
            </p>
          </section>
        )}
      </div>
    </section>
  );
}
