import type {
  ConsoleAction,
  ConsoleRecord,
  ConsoleState,
} from "./console-types";
import {
  canAccept,
  isDirty,
  scopeIsValid,
  initialRecord,
  newRecord,
} from "./console-fixtures";
import { isDraftReady } from "./fixture-data";

function append(
  record: ConsoleRecord,
  title: string,
  detail: string,
): ConsoleRecord {
  const id = (record.history.at(-1)?.id ?? 0) + 1;
  return {
    ...record,
    history: [
      ...record.history.slice(-49),
      { id, title, detail, revision: record.revision },
    ],
  };
}

function invalidate(record: ConsoleRecord): ConsoleRecord {
  return {
    ...record,
    reviewed: false,
    confirmed: false,
    approved: false,
    offered: false,
    withdrawn: false,
    revoked: false,
  };
}

function commit(record: ConsoleRecord): ConsoleRecord {
  if (!isDraftReady(record.draft) || !isDirty(record)) return record;
  return append(
    {
      ...invalidate(record),
      committed: { ...record.draft },
      revision: isDraftReady(record.committed) ? record.revision + 1 : 1,
    },
    "New fixture version",
    "Changed fields captured in this tab. No server version was created.",
  );
}

function analyze(
  record: ConsoleRecord,
  status: ConsoleRecord["analysis"],
): ConsoleRecord {
  if (status === "running" && !isDraftReady(record.draft)) return record;
  const next = status === "running" ? commit(record) : record;
  return append(
    { ...invalidate(next), analysis: status, phase: 0, candidate: false },
    status === "running"
      ? "Fixture analysis started"
      : status === "error"
        ? "Fixture analysis interrupted"
        : status === "cancelled"
          ? "Fixture analysis cancelled"
          : "Analysis reset",
    "Scripted visual scenario; no model request or server job.",
  );
}

function decision(record: ConsoleRecord, action: ConsoleAction): ConsoleRecord {
  switch (action.type) {
    case "review":
      if (
        record.analysis !== "ready" ||
        !isDraftReady(record.draft) ||
        isDirty(record) ||
        record.reviewActor !== "reviewer"
      )
        return record;
      return append(
        { ...invalidate(record), reviewed: true, campaignActor: "creator" },
        "Independent demo review recorded",
        "Fictional reviewer Mira Chen reviewed this exact fixture version.",
      );
    case "reviewChanges":
      return append(
        { ...invalidate(record) },
        "Review changes requested",
        "Creator must revise the fixture before another review.",
      );

    default:
      return campaignDecision(record, action);
  }
}

function campaignDecision(
  record: ConsoleRecord,
  action: ConsoleAction,
): ConsoleRecord {
  switch (action.type) {
    case "offer":
      return offer(record);
    case "accept":
      if (!canAccept(record)) return record;
      return append(
        { ...record, approved: true },
        "Demo campaign accepted",
        "Named recipient accepted this offer; current eligibility remains separate.",
      );
    case "campaignChanges":
      if (
        !record.offered ||
        record.revoked ||
        record.campaignActor !== "recipient"
      )
        return record;
      return append(
        { ...record, approved: false, confirmed: false, withdrawn: true },
        "Recipient requested changes",
        "Independent persona review remains; the creator must issue a new offer.",
      );
    case "revoke":
      if (
        !record.offered ||
        record.revoked ||
        record.campaignActor !== "creator"
      )
        return record;
      return append(
        { ...record, revoked: true, approved: false, confirmed: false },
        "Demo campaign revoked",
        "This offer cannot be accepted again. A new owner offer is required.",
      );
    default:
      return record;
  }
}

function changeRecord(
  record: ConsoleRecord,
  action: ConsoleAction,
): ConsoleRecord {
  switch (action.type) {
    case "edit":
      return {
        ...invalidate(record),
        draft: {
          ...record.draft,
          [action.key]: action.value.slice(0, action.key === "name" ? 80 : 500),
        },
        analysis: "idle",
        phase: 0,
        candidate: false,
        comment: "",
      };
    case "commit":
      return commit(record);
    case "analysis":
      return analyze(record, action.status);
    case "phase":
      if (
        record.id !== action.recordId ||
        record.analysis !== "running" ||
        !Number.isInteger(action.index) ||
        action.index <= record.phase ||
        action.index > 5
      )
        return record;
      return action.index >= 5
        ? append(
            { ...record, phase: 5, analysis: "ready" },
            "Fixture findings ready",
            "One palette candidate and two evidence gaps; human review remains required.",
          )
        : { ...record, phase: action.index };
    case "note":
      return { ...invalidate(record), comment: action.value.slice(0, 500) };

    default:
      return changePresentation(record, action);
  }
}

function changePresentation(
  record: ConsoleRecord,
  action: ConsoleAction,
): ConsoleRecord {
  switch (action.type) {
    case "candidate":
      return {
        ...record,
        candidate: action.value && record.analysis === "ready",
      };
    case "comparison":
      return {
        ...record,
        comparison: Math.max(0, Math.min(100, action.value)),
      };
    case "confirm":
      return { ...record, confirmed: action.value };
    case "scope":
      return {
        ...record,
        scope: { ...record.scope, [action.key]: action.value },
        offered: false,
        approved: false,
        confirmed: false,
        withdrawn: false,
        revoked: false,
      };
    case "campaignActor":
      return { ...record, campaignActor: action.actor, confirmed: false };
    case "reviewActor":
      return { ...record, reviewActor: action.actor };
    case "window":
      return { ...record, window: action.value };
    default:
      return decision(record, action);
  }
}

export function consoleReducer(
  state: ConsoleState,
  action: ConsoleAction,
): ConsoleState {
  switch (action.type) {
    case "restore":
      return {
        ...state,
        selected: action.selected,
        records: action.records.map((item) => ({
          ...initialRecord(item.variant),
          ...item,
          committed: { ...item.draft },
        })),
      };
    case "new":
      return state.records.length >= 12
        ? state
        : {
            ...state,
            records: [
              ...cancelScans(state.records),
              newRecord(state.records.length),
            ],
            selected: state.records.length,
            step: 1,
            drawer: null,
          };
    case "select": {
      if (!state.records[action.index]) return state;
      const records = cancelScans(state.records);
      return {
        ...state,
        selected: action.index,
        records,
        step: 1,
        publicView: true,
        drawer: null,
      };
    }

    default:
      return navigate(state, action);
  }
}

function navigate(state: ConsoleState, action: ConsoleAction): ConsoleState {
  switch (action.type) {
    case "sidebar":
      return { ...state, sidebarCollapsed: action.value };
    case "step":
      return {
        ...state,
        step: Math.max(0, Math.min(4, action.step)),
      };
    case "filter":
      return { ...state, filter: action.value };
    case "search":
      return { ...state, search: action.value.slice(0, 80) };
    case "publicView":
      return { ...state, publicView: action.value };
    case "drawer":
      return { ...state, drawer: action.value };
    case "question":
      return { ...state, assistantQuestion: action.value, drawer: "assistant" };
    default:
      return {
        ...state,
        records: state.records.map((record, index) =>
          index === state.selected ? changeRecord(record, action) : record,
        ),
      };
  }
}

function cancelScans(records: ConsoleRecord[]): ConsoleRecord[] {
  return records.map((record) =>
    record.analysis === "running" ? analyze(record, "cancelled") : record,
  );
}

function offer(record: ConsoleRecord): ConsoleRecord {
  if (
    !record.reviewed ||
    isDirty(record) ||
    !scopeIsValid(record.scope) ||
    record.campaignActor !== "creator" ||
    record.window === "expired"
  )
    return record;
  return append(
    {
      ...record,
      offered: true,
      confirmed: false,
      approved: false,
      revoked: false,
      withdrawn: false,
    },
    "New demo campaign offer",
    "North Studio offered the canonical study to fictional Solstice Goods.",
  );
}
