import { useCallback, useEffect, useRef, useState } from "react";
import type {
  RecordTarget,
  RecordSection,
  WorkspacePage,
} from "./workspace-pages";
import type { WorkspacePanelKind } from "./workspace-console";

type Selection = { owner: string; target: RecordTarget };
type LoadedVersion = { owner: string; id: string; revision: number };
function useWorkspaceSelection(owner: string) {
  const [selected, setSelected] = useState<Selection | null>(null);
  const [showRecord, setShowRecord] = useState(false),
    [selectionOwner, setSelectionOwner] = useState(owner);
  const previous = useRef<LoadedVersion | null>(null);
  if (selectionOwner !== owner) {
    setSelectionOwner(owner);
    setSelected(null);
    setShowRecord(false);
  }
  const target = selected?.owner === owner ? selected.target : null;
  const loaded = useCallback(
    (id: string, revision: number) => {
      previous.current = { owner, id, revision };
    },
    [owner],
  );
  function choose(id: string, section: RecordSection = "Overview") {
    previous.current = null;
    setSelected({ owner, target: { id, revision: null, section } });
  }
  function version(revision: number | null) {
    if (target) setSelected({ owner, target: { ...target, revision } });
  }
  function pin() {
    const row = previous.current;
    if (
      target &&
      target.revision === null &&
      row?.owner === owner &&
      row.id === target.id
    )
      version(row.revision);
  }
  return {
    target,
    showRecord,
    setShowRecord,
    loaded,
    choose,
    version,
    pin,
    clearSelection: () => setSelected(null),
  };
}
function useWorkspacePanel() {
  const [panel, setPanel] = useState<WorkspacePanelKind>(null);
  const [collapsed, setCollapsed] = useState(false);
  const close = useCallback(() => setPanel(null), []);
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPanel("commands");
      }
    };
    document.addEventListener("keydown", shortcut);
    return () => document.removeEventListener("keydown", shortcut);
  }, []);
  return { panel, setPanel, collapsed, setCollapsed, close };
}
export default function useWorkspaceControls(owner: string) {
  const [page, setPage] = useState<WorkspacePage>("Records");
  const selection = useWorkspaceSelection(owner),
    panels = useWorkspacePanel();
  function navigate(next: WorkspacePage) {
    selection.pin();
    setPage(next);
    if (next === "Records") selection.setShowRecord(false);
  }
  function openRecord(id: string, section: RecordSection = "Overview") {
    selection.choose(id, section);
    setPage("Records");
    selection.setShowRecord(true);
  }
  return { ...selection, ...panels, page, navigate, openRecord };
}
