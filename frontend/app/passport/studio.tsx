"use client";
import { useState } from "react";
import { SavedSourceContext, type SavedPersonaSource } from "./saved-source";
import WorkspaceConsole from "./workspace-console";
import {
  WriteDraftContext,
  type WriteDraftStore,
} from "./prepared-write-state";

export default function PassportStudio({
  savedSource = null,
  sessionAction,
}: {
  savedSource?: SavedPersonaSource | null;
  sessionAction?: { label: string; run: () => void };
}) {
  const [writeDrafts] = useState<WriteDraftStore>(() => new Map());
  return (
    <SavedSourceContext.Provider value={savedSource}>
      <WriteDraftContext.Provider value={writeDrafts}>
        <WorkspaceConsole sessionAction={sessionAction} />
      </WriteDraftContext.Provider>
    </SavedSourceContext.Provider>
  );
}
