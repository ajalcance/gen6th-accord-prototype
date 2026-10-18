import { beforeEach, describe, expect, it } from "vitest";
import { initialConsole } from "./legacy-passport/console-fixtures";
import { consoleReducer } from "./legacy-passport/console-reducer";
import {
  readWorkspace,
  writeWorkspace,
  STORAGE_KEY,
  publicFixture,
} from "./legacy-passport/console-storage";

beforeEach(() => localStorage.clear());
describe("draft persistence never restores approval authority", () => {
  it("writes an explicit draft-only allowlist", () => {
    const records = initialConsole().records;
    records[0] = {
      ...records[0],
      approved: true,
      reviewed: true,
      comment: "Private evidence note",
    };
    writeWorkspace(records, 1);
    const raw = localStorage.getItem(STORAGE_KEY)!;
    expect(raw).not.toContain("Private evidence note");
    expect(raw).not.toContain("approved");
    expect(Object.keys(JSON.parse(raw).records[0])).toEqual([
      "id",
      "variant",
      "draft",
    ]);
  });
  it("drops forged actors and decisions during restoration", () => {
    const state = initialConsole();
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        schema: 2,
        selected: 0,
        records: state.records.map((record) => ({
          ...record,
          reviewed: true,
          approved: true,
          reviewActor: "creator",
          comment: "Forged note",
        })),
      }),
    );
    const saved = readWorkspace(state.records)!;
    const restored = consoleReducer(state, { type: "restore", ...saved });
    expect(restored.records[0]).toMatchObject({
      reviewed: false,
      approved: false,
      comment: "",
      analysis: "idle",
      reviewActor: "reviewer",
    });
  });
  it.each([-1, 3, 0.5, "0"])(
    "rejects invalid selected index %s",
    (selected) => {
      writeWorkspace(initialConsole().records, 0);
      const value = JSON.parse(localStorage.getItem(STORAGE_KEY)!);
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...value, selected }));
      expect(() => readWorkspace(initialConsole().records)).toThrow();
    },
  );
  it.each(["id", "variant", "draft"])("rejects malformed record %s", (key) => {
    writeWorkspace(initialConsole().records, 0);
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY)!);
    value.records[0][key] = key === "variant" ? 9 : "Invalid";
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    expect(() => readWorkspace(initialConsole().records)).toThrow();
  });
  it("rejects oversized and malformed payloads", () => {
    for (const raw of [
      "x".repeat(32769),
      "invalid",
      "null",
      JSON.stringify({ schema: 9, records: [] }),
    ]) {
      localStorage.setItem(STORAGE_KEY, raw);
      expect(() => readWorkspace(initialConsole().records)).toThrow();
    }
  });
  it("exports committed public fields without private notes or unsigned claims", () => {
    const record = initialConsole().records[0];
    const exported = publicFixture({
      ...record,
      draft: { ...record.draft, bio: "Uncommitted text" },
      comment: "Private note",
    });
    expect(exported).toMatchObject({
      signed: false,
      demo: true,
      biography: record.committed.bio,
    });
    expect(JSON.stringify(exported)).not.toContain("Private note");
    expect(JSON.stringify(exported)).not.toContain("Uncommitted text");
    expect(Object.keys(exported)).toEqual([
      "demo",
      "signed",
      "persona",
      "biography",
      "ai_disclosure",
      "version",
      "review",
      "campaign",
    ]);
  });
});
