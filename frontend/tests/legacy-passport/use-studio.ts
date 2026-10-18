"use client";

import { useEffect, useReducer, useRef, useState, type Dispatch } from "react";
import { initialConsole, isDirty, SCAN_DURATION_MS } from "./console-fixtures";
import { consoleReducer } from "./console-reducer";
import {
  readWorkspace,
  writeWorkspace,
  downloadPublicFixture,
} from "./console-storage";
import { isDraftReady, type Draft } from "./fixture-data";
import type {
  AnalysisStatus,
  DrawerKind,
  ScopeDraft,
  ConsoleAction,
  ConsoleState,
  ConsoleRecord,
} from "./console-types";

export function useStudio(initialState: ConsoleState = initialConsole()) {
  const [state, dispatch] = useReducer(consoleReducer, initialState);
  const record = state.records[state.selected];
  const { storage, persist } = useWorkspaceStorage(state, dispatch);
  useScanClock(record, dispatch);
  const actions = studioActions(state, dispatch, persist);
  return {
    ...state,
    ...record,
    record,
    storage,
    dispatch,
    ...actions,
    selected: state.selected,
    canReview: isDraftReady(record.draft),
    dirty: isDirty(record),
    ...studioBindings(record, dispatch),
  };
}
export type StudioState = ReturnType<typeof useStudio>;

function useWorkspaceStorage(
  state: ConsoleState,
  dispatch: Dispatch<ConsoleAction>,
) {
  const [storage, setStorage] = useState("Draft stays in this browser only");
  const edited = useRef(false);
  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (edited.current) return;
      try {
        const saved = readWorkspace(initialConsole().records);
        if (saved) {
          dispatch({ type: "restore", ...saved });
          setStorage("Demo drafts restored; decisions require a new review");
        }
      } catch {
        setStorage("Browser storage unavailable; keep this tab open");
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, [dispatch]);
  function persist(records = state.records, selected = state.selected) {
    edited.current = true;
    try {
      writeWorkspace(records, selected);
      setStorage("Demo draft saved in this browser");
    } catch {
      setStorage("Browser storage unavailable; keep this tab open");
    }
  }

  return { storage, persist };
}

function useScanClock(
  record: ConsoleRecord,
  dispatch: Dispatch<ConsoleAction>,
) {
  useEffect(() => {
    if (record.analysis !== "running") return;
    const timers = [1, 2, 3, 4, 5].map((index) =>
      window.setTimeout(
        () => dispatch({ type: "phase", index, recordId: record.id }),
        (SCAN_DURATION_MS * index) / 5,
      ),
    );
    return () => timers.forEach(window.clearTimeout);
  }, [record.id, record.analysis, dispatch]);
}

function studioActions(
  state: ConsoleState,
  dispatch: Dispatch<ConsoleAction>,
  persist: (records?: ConsoleRecord[], selected?: number) => void,
) {
  const record = state.records[state.selected];
  function update(key: keyof Draft, value: string) {
    const action = { type: "edit" as const, key, value };
    persist(consoleReducer(state, action).records);
    dispatch(action);
  }
  function setSelected(index: number) {
    persist(state.records, index);
    dispatch({ type: "select", index });
  }
  function createPersona() {
    const next = consoleReducer(state, { type: "new" });
    persist(next.records, next.selected);
    dispatch({ type: "new" });
  }
  function recordReview() {
    const next = consoleReducer(state, { type: "review" });
    if (
      next.records[state.selected] === record ||
      !next.records[state.selected].reviewed
    )
      return false;
    dispatch({ type: "review" });
    return true;
  }
  function acceptScope() {
    const next = consoleReducer(state, { type: "accept" });
    if (
      next.records[state.selected] === record ||
      !next.records[state.selected].approved
    )
      return false;
    dispatch({ type: "accept" });
    return true;
  }

  return { update, setSelected, createPersona, recordReview, acceptScope };
}

function studioBindings(
  record: ConsoleRecord,
  dispatch: Dispatch<ConsoleAction>,
) {
  return {
    setStep: (step: number) => dispatch({ type: "step", step }),
    setFilter: (value: string) => dispatch({ type: "filter", value }),
    setSearch: (value: string) => dispatch({ type: "search", value }),
    setAnalysis: (status: AnalysisStatus) =>
      dispatch({ type: "analysis", status }),
    setCandidate: (value: boolean) => dispatch({ type: "candidate", value }),
    setComparison: (value: number) => dispatch({ type: "comparison", value }),
    setComment: (value: string) => dispatch({ type: "note", value }),
    setConfirmed: (value: boolean) => dispatch({ type: "confirm", value }),
    setPublicView: (value: boolean) => dispatch({ type: "publicView", value }),
    setDrawer: (value: DrawerKind) => dispatch({ type: "drawer", value }),
    setScope: (key: keyof ScopeDraft, value: string) =>
      dispatch({ type: "scope", key, value }),
    ask: (value: string) => dispatch({ type: "question", value }),
    invalidate: () => dispatch({ type: "reviewChanges" }),
    download: () => downloadPublicFixture(record),
  };
}
