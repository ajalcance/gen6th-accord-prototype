import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import PassportStudio from "./legacy-passport-studio";
import { initialConsole } from "./legacy-passport/console-fixtures";
import GovernanceWorkspace from "./legacy-passport/governance-workspace";
import GovernanceReviews from "./legacy-passport/governance-reviews";
import GovernanceEvidence from "./legacy-passport/governance-evidence";
import GovernanceAudit from "../app/passport/governance-audit";
import {
  EXAMPLE_REVIEWS,
  EXAMPLE_VERSIONS,
  EXAMPLE_EVIDENCE,
  EXAMPLE_WORKSPACE,
  exampleAudit,
} from "./legacy-passport/governance-fixtures";
import { personaGateway } from "../lib/persona-gateway";
import { ApiError } from "../lib/api-client";
import type { Draft } from "./legacy-passport/fixture-data";

const draft: Draft = {
  name: "Preserved fictional draft",
  bio: "Fictional biography",
  contribution: "Hand edited composition",
  disclosure: "No AI model ran",
};
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});
function click(name: string | RegExp) {
  fireEvent.click(screen.getByRole("button", { name }));
}
function open() {
  return render(
    <GovernanceWorkspace draft={draft} close={vi.fn()} connection={vi.fn()} />,
  );
}
function condition(value: string) {
  fireEvent.click(screen.getByText("Preview conditions"));
  fireEvent.change(screen.getByLabelText("Read condition"), {
    target: { value },
  });
}

describe("visible governance records and recovery reads", () => {
  it("shows the separate preview boundary and version snapshots without HTTP", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    open();
    expect(
      await screen.findByRole("heading", { name: "Version 3" }),
    ).toBeDefined();
    expect(screen.getByText(/not your selected persona/)).toBeDefined();
    expect(screen.getByText("Unsigned")).toBeDefined();
    fireEvent.change(screen.getByLabelText("Version"), {
      target: { value: "1" },
    });
    expect(
      await screen.findByRole("heading", { name: "Version 1" }),
    ).toBeDefined();
    expect(screen.getByText("A fictional editorial character.")).toBeDefined();
    expect(screen.queryByRole("heading", { name: "Version 3" })).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
  it("paginates exact-version reviews and exposes pending versus present audit references", async () => {
    open();
    click("Reviews");
    expect(
      await screen.findByRole("heading", { name: "Review approved" }),
    ).toBeDefined();
    click("Inspect audit reference");
    expect(await screen.findByText("Audit pending")).toBeDefined();
    const older = screen.getByRole("button", { name: "Older reviews" });
    older.focus();
    fireEvent.click(older);
    expect(
      await screen.findByRole("heading", { name: "Changes requested" }),
    ).toBeDefined();
    expect(screen.queryByText("Audit pending")).toBeNull();
    expect(document.activeElement).toBe(older);
    click("Inspect audit reference");
    expect(await screen.findByText("Audit entry present")).toBeDefined();
    expect(
      screen.getByText(/Chain integrity and signing are not verified/),
    ).toBeDefined();
    click("Newest reviews");
    expect(
      await screen.findByRole("heading", { name: "Review approved" }),
    ).toBeDefined();
    fireEvent.change(screen.getByLabelText("Reviewed version"), {
      target: { value: "3" },
    });
    expect(
      await screen.findByRole("heading", { name: "No independent review yet" }),
    ).toBeDefined();
    expect(
      screen.queryByRole("heading", { name: "Review approved" }),
    ).toBeNull();
  });
  it("shows blocked scope separately from historical acceptance and pages older decisions", async () => {
    open();
    click("Campaign");
    expect(await screen.findByText("Use blocked")).toBeDefined();
    expect(
      await screen.findByRole("heading", { name: "Accepted · historical" }),
    ).toBeDefined();
    expect(
      screen.getByText(/Historical acceptance does not authorize current use/),
    ).toBeDefined();
    click("Older decisions");
    expect(
      await screen.findByRole("heading", { name: "Changes requested" }),
    ).toBeDefined();
    expect(
      screen.queryByRole("heading", { name: "Accepted · historical" }),
    ).toBeNull();
    click("Newest decisions");
    expect(
      await screen.findByRole("heading", { name: "Revoked" }),
    ).toBeDefined();
  });
  it("distinguishes all evidence states without private payload, retention or rights claims", async () => {
    open();
    click("Evidence");
    for (const name of [
      "Quarantined",
      "Inspection passed",
      "Rejected",
      "Expired",
    ])
      expect(await screen.findByRole("heading", { name })).toBeDefined();
    expect(screen.getByText(/does not grant rights/)).toBeDefined();
    expect(screen.getByText(/Expiry does not prove deletion/)).toBeDefined();
    expect(
      screen.queryByRole("button", { name: /download|upload/i }),
    ).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
  });
  it.each(["Versions", "Reviews", "Campaign", "Evidence"])(
    "gives a useful empty state for %s",
    async (section) => {
      open();
      if (section !== "Versions") click(section);
      condition("empty");
      expect(
        await screen.findByRole("heading", { name: /^No / }),
      ).toBeDefined();
      click("Restore populated example");
      expect(screen.queryByRole("heading", { name: /^No / })).toBeNull();
    },
  );
  it.each(["Versions", "Reviews", "Campaign", "Evidence"])(
    "clears %s records on permission loss and restores only the example",
    async (section) => {
      open();
      if (section !== "Versions") click(section);
      await screen.findAllByRole("heading", { level: 3 });
      condition("denied");
      expect((await screen.findAllByRole("alert")).length).toBeGreaterThan(0);
      expect(screen.queryByText("Unsigned")).toBeNull();
      expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
      expect(
        screen.getByRole("button", { name: "Connection details" }),
      ).toBeDefined();
      click("Restore populated example");
      expect(screen.queryByRole("alert")).toBeNull();
    },
  );
  it("provides explicit unavailable retry and a working connection action", async () => {
    const connection = vi.fn();
    render(
      <GovernanceWorkspace
        draft={draft}
        close={vi.fn()}
        connection={connection}
      />,
    );
    condition("unavailable");
    expect(await screen.findByRole("alert")).toBeDefined();
    click("Try again");
    expect(await screen.findByRole("alert")).toBeDefined();
    fireEvent.change(screen.getByLabelText("Read condition"), {
      target: { value: "denied" },
    });
    await screen.findByRole("alert");
    click("Connection details");
    expect(connection).toHaveBeenCalledOnce();
  });
  it("rejects a creator presented as an independent reviewer", async () => {
    const gateway = personaGateway(EXAMPLE_WORKSPACE, async () => ({
      items: [
        {
          ...EXAMPLE_REVIEWS[0],
          reviewer_ref: EXAMPLE_VERSIONS[1].creator_ref,
        },
      ],
      next_before_ordinal: null,
    }));
    render(<GovernanceReviews gateway={gateway} />);
    expect(await screen.findByRole("alert")).toBeDefined();
    expect(
      screen.queryByRole("heading", { name: "Review approved" }),
    ).toBeNull();
  });
  it("rejects evidence metadata bound to another version", async () => {
    const gateway = personaGateway(
      EXAMPLE_WORKSPACE,
      async (_operation, _workspace, raw) => ({
        ...EXAMPLE_EVIDENCE[0],
        id: (raw as { evidence_id: string }).evidence_id,
        version_id: EXAMPLE_VERSIONS[0].version_id,
      }),
    );
    render(<GovernanceEvidence gateway={gateway} empty={false} />);
    expect(await screen.findAllByRole("alert")).toHaveLength(1);
    expect(screen.queryByRole("heading", { name: "Quarantined" })).toBeNull();
  });
  it("clears the entire evidence view when one item loses permission", async () => {
    const gateway = personaGateway(
      EXAMPLE_WORKSPACE,
      async (_operation, _workspace, raw) => {
        const id = (raw as { evidence_id: string }).evidence_id;
        if (id === EXAMPLE_EVIDENCE[0].id)
          throw new ApiError("Example access lost", 403);
        return EXAMPLE_EVIDENCE.find((row) => row.id === id);
      },
    );
    render(<GovernanceEvidence gateway={gateway} empty={false} />);
    expect(await screen.findByRole("alert")).toBeDefined();
    for (const name of ["Inspection passed", "Rejected", "Expired"])
      expect(screen.queryByRole("heading", { name })).toBeNull();
  });
  it.each(["actor", "version", "event", "time", "fractional-time"])(
    "rejects an audit reference with mismatched %s",
    async (field) => {
      const row = EXAMPLE_REVIEWS[0];
      const value = exampleAudit(row.id);
      if (field === "actor") value.anchor.actor_ref = "other-reviewer";
      if (field === "version")
        value.anchor.version_id = EXAMPLE_VERSIONS[0].version_id;
      if (field === "event") value.anchor.event_id = "f".repeat(32);
      if (field === "time") value.anchor.recorded_at = "2026-10-02T03:20:00Z";
      if (field === "fractional-time")
        value.anchor.recorded_at = "2026-10-02T02:20:00.000001Z";
      render(
        <GovernanceAudit
          gateway={personaGateway(EXAMPLE_WORKSPACE, async () => value)}
          binding={{
            recordId: row.id,
            kind: "review",
            versionId: row.version_id,
            actor: row.reviewer_ref,
            eventId: row.event_id,
            recordedAt: row.recorded_at,
          }}
        />,
      );
      click("Inspect audit reference");
      expect(await screen.findByRole("alert")).toBeDefined();
      expect(screen.queryByText("Audit pending")).toBeNull();
    },
  );
});

describe("five-screen access and focus", () => {
  it("takes an empty-state next action to the real System Capture screen without fabricating a save", async () => {
    render(<PassportStudio initialState={initialConsole()} />);
    click("Evidence & decisions");
    condition("empty");
    await screen.findByRole("heading", { name: "No saved versions" });
    click("Go to System Capture");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByRole("form", { name: "System Capture" })).toBeDefined();
    expect(screen.getByText(/fixture-v1/).textContent).toContain("local only");
  });
  it("opens governance from every screen, closes with Escape and returns focus", async () => {
    render(<PassportStudio initialState={initialConsole()} />);
    for (const screenName of [
      "Records",
      "System Capture",
      "Analysis & review",
      "Campaign approval",
      "Public passport",
    ]) {
      click(screenName);
      const trigger = screen.getByRole("button", {
        name: "Evidence & decisions",
      });
      trigger.focus();
      fireEvent.click(trigger);
      expect(
        await within(screen.getByRole("dialog")).findByRole("heading", {
          name: "Version 3",
        }),
      ).toBeDefined();
      expect(
        within(screen.getByRole("dialog")).getByText(
          "FICTIONAL GOVERNANCE EXAMPLES",
        ),
      ).toBeDefined();
      const close = screen.getByRole("button", { name: "Close panel" });
      expect(document.activeElement).toBe(close);
      fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
      expect(document.activeElement).not.toBe(close);
      fireEvent.keyDown(document, { key: "Escape" });
      expect(screen.queryByRole("dialog")).toBeNull();
      expect(document.activeElement).toBe(trigger);
    }
  });
  it("discovers governance in quick actions without changing a draft", async () => {
    render(<PassportStudio initialState={initialConsole()} />);
    click("Quick actions");
    const search = within(screen.getByRole("dialog")).getByRole("searchbox");
    fireEvent.change(search, { target: { value: "Evidence" } });
    fireEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", {
        name: "Evidence & decisions",
      }),
    );
    expect(
      await screen.findByRole("heading", { name: "Version 3" }),
    ).toBeDefined();
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "Close panel" }),
    );
  });
});
