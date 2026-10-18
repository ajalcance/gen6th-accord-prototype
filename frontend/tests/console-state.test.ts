import { describe, expect, it } from "vitest";
import { consoleReducer as reduce } from "./legacy-passport/console-reducer";
import {
  initialConsole,
  canAccept,
  campaignBlocks,
  scopeIsValid,
} from "./legacy-passport/console-fixtures";
import type {
  ConsoleAction,
  ConsoleState,
} from "./legacy-passport/console-types";

function journey(...actions: ConsoleAction[]): ConsoleState {
  return actions.reduce(reduce, initialConsole());
}
function reviewed(): ConsoleState {
  return journey(
    { type: "analysis", status: "running" },
    { type: "phase", index: 5, recordId: "nova" },
    { type: "review" },
  );
}
function accepted(): ConsoleState {
  return [
    { type: "offer" },
    { type: "campaignActor", actor: "recipient" },
    { type: "confirm", value: true },
    { type: "accept" },
  ].reduce(
    (state, action) => reduce(state, action as ConsoleAction),
    reviewed(),
  );
}
describe("bounded independent fixture state", () => {
  it("keeps edits and decisions scoped to one persona", () => {
    const edited = reduce(reviewed(), {
      type: "edit",
      key: "name",
      value: "New fictional Nova",
    });
    const switched = reduce(edited, { type: "select", index: 1 });
    expect(switched.records[0].draft.name).toBe("New fictional Nova");
    expect(switched.records[0].reviewed).toBe(false);
    expect(switched.records[1].draft.name).toBe("Iris Sol");
  });
  it("creates blank records and caps the workspace at twelve", () => {
    let state = initialConsole();
    for (let i = 0; i < 20; i++) state = reduce(state, { type: "new" });
    expect(state.records).toHaveLength(12);
    expect(state.records[3].id).toBe("local-4");
    expect(state.records[3].draft.name).toBe("");
    expect(state.selected).toBe(11);
  });
  it("captures exact versions without leaking dirty edits into committed fields", () => {
    const edited = reduce(reviewed(), {
      type: "edit",
      key: "bio",
      value: "Changed fiction",
    });
    expect(edited.records[0].committed.bio).not.toBe("Changed fiction");
    const committed = reduce(edited, { type: "commit" });
    expect(committed.records[0].revision).toBe(2);
    expect(committed.records[0].committed.bio).toBe("Changed fiction");
    expect(reduce(committed, { type: "commit" }).records[0].revision).toBe(2);
  });
  it.each(["select", "new", "edit"] as const)(
    "cancels running work on %s and refuses stale completion",
    (kind) => {
      let state = journey({ type: "analysis", status: "running" });
      state = reduce(
        state,
        kind === "select"
          ? { type: kind, index: 1 }
          : kind === "edit"
            ? { type: kind, key: "bio", value: "Changed" }
            : { type: kind },
      );
      state = reduce(state, { type: "phase", index: 5, recordId: "nova" });
      expect(state.records[0].analysis).not.toBe("ready");
      expect(state.records[0].reviewed).toBe(false);
    },
  );
  it("rejects out-of-order, fractional and cross-record progress", () => {
    const state = journey(
      { type: "analysis", status: "running" },
      { type: "phase", index: 2, recordId: "nova" },
    );
    for (const [index, recordId] of [
      [1, "nova"],
      [2.5, "nova"],
      [6, "nova"],
      [5, "iris"],
    ] as const) {
      expect(reduce(state, { type: "phase", index, recordId }).records[0]).toBe(
        state.records[0],
      );
    }
  });
  it("refuses self-review and incomplete review", () => {
    const ready = journey(
      { type: "analysis", status: "running" },
      { type: "phase", index: 5, recordId: "nova" },
      { type: "reviewActor", actor: "creator" },
      { type: "review" },
    );
    expect(ready.records[0].reviewed).toBe(false);
    expect(journey({ type: "review" }).records[0].reviewed).toBe(false);
  });
  it("caps local history without reusing entry identities", () => {
    let state = initialConsole();
    for (let i = 0; i < 65; i++)
      state = reduce(state, { type: "analysis", status: "error" });
    expect(state.records[0].history).toHaveLength(50);
    expect(state.records[0].history.at(-1)?.id).toBe(66);
  });
});
describe("campaign scenario follows backend decision boundaries", () => {
  it("requires owner offer, recipient actor and fresh confirmation", () => {
    const state = reviewed();
    expect(reduce(state, { type: "accept" }).records[0].approved).toBe(false);
    const offer = reduce(state, { type: "offer" });
    expect(canAccept({ ...offer.records[0], confirmed: true })).toBe(false);
    expect(accepted().records[0].approved).toBe(true);
  });
  it("separates historical acceptance from current eligibility", () => {
    const state = accepted();
    expect(campaignBlocks(state.records[0])).toContain(
      "The campaign window has not started.",
    );
    const active = reduce(state, { type: "window", value: "active" });
    expect(campaignBlocks(active.records[0])).toEqual([]);
    const expired = reduce(active, { type: "window", value: "expired" });
    expect(expired.records[0].approved).toBe(true);
    expect(campaignBlocks(expired.records[0])).toContain(
      "The campaign window has expired.",
    );
  });
  it("preserves persona review when recipient requests campaign changes", () => {
    const state = reduce(accepted(), { type: "campaignChanges" });
    expect(state.records[0]).toMatchObject({
      reviewed: true,
      approved: false,
      withdrawn: true,
      confirmed: false,
    });
    expect(reduce(state, { type: "accept" }).records[0].approved).toBe(false);
  });
  it("permits only the creator to revoke and requires a new offer", () => {
    const state = accepted();
    expect(reduce(state, { type: "revoke" }).records[0].revoked).toBe(false);
    const creator = reduce(state, { type: "campaignActor", actor: "creator" });
    const revoked = reduce(creator, { type: "revoke" });
    expect(revoked.records[0]).toMatchObject({
      revoked: true,
      approved: false,
    });
    const recipient = reduce(revoked, {
      type: "campaignActor",
      actor: "recipient",
    });
    expect(reduce(recipient, { type: "offer" }).records[0].revoked).toBe(true);
    expect(reduce(revoked, { type: "offer" }).records[0].revoked).toBe(false);
  });
  it("clears an offer on scope edits while preserving the independent review", () => {
    const state = reduce(accepted(), {
      type: "scope",
      key: "purpose",
      value: "New use",
    });
    expect(state.records[0]).toMatchObject({
      reviewed: true,
      offered: false,
      approved: false,
      confirmed: false,
    });
  });
  it("refuses new offers and acceptance after expiry", () => {
    const expired = reduce(reviewed(), { type: "window", value: "expired" });
    expect(reduce(expired, { type: "offer" }).records[0].offered).toBe(false);
    expect(
      canAccept({
        ...accepted().records[0],
        approved: false,
        window: "expired",
      }),
    ).toBe(false);
  });
  it.each(["", "2026-02-30", "not-a-date", "2026-11-15"])(
    "refuses malformed or empty duration %s",
    (startsAt) => {
      expect(
        scopeIsValid({ ...initialConsole().records[0].scope, startsAt }),
      ).toBe(false);
    },
  );
  it("rejects overlong windows and missing purpose or conditions", () => {
    const scope = initialConsole().records[0].scope;
    expect(scopeIsValid({ ...scope, endsAt: "2028-11-15" })).toBe(false);
    expect(scopeIsValid({ ...scope, purpose: " " })).toBe(false);
    expect(scopeIsValid({ ...scope, conditions: "x".repeat(501) })).toBe(false);
  });
});
