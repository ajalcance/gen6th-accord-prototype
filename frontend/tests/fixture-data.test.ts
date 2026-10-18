import { afterEach, describe, expect, it, vi } from "vitest";
import { readDraft } from "./legacy-passport/fixture-data";
import {
  publicFixture,
  downloadPublicFixture,
} from "./legacy-passport/console-storage";
import { initialConsole } from "./legacy-passport/console-fixtures";

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
describe("fixture data boundary", () => {
  it("rejects invalid stored shapes and bounds restored fields", () => {
    localStorage.setItem("accord-h1-draft", JSON.stringify({ name: 42 }));
    expect(readDraft()).toBeNull();
    localStorage.setItem(
      "accord-h1-draft",
      JSON.stringify({
        name: "x".repeat(100),
        bio: "y".repeat(600),
        contribution: "z".repeat(600),
      }),
    );
    expect(readDraft()?.name.length).toBe(80);
    expect(readDraft()?.bio.length).toBe(500);
    expect(readDraft()?.contribution.length).toBe(500);
  });
  it("exports a declared unsigned demo with only allowed fields", () => {
    const record = initialConsole().records[0];
    expect(publicFixture(record)).toEqual({
      demo: true,
      signed: false,
      persona: "Nova Vale",
      biography: record.committed.bio,
      ai_disclosure: record.committed.disclosure,
      version: "fixture-v1",
      campaign: null,
      review: "pending",
    });
    expect(publicFixture({ ...record, approved: true }).campaign).toBe(
      "A quieter kind of summer",
    );
  });
  it("downloads the fixture and releases its temporary object URL", () => {
    const createObjectURL = vi.fn((blob: Blob) => {
      expect(blob).toBeInstanceOf(Blob);
      return "blob:fictional-fixture";
    });
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});
    downloadPublicFixture(initialConsole().records[0]);
    expect(createObjectURL.mock.calls[0]?.[0]).toBeInstanceOf(Blob);
    expect(click).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:fictional-fixture");
  });
  it("releases the object URL even if the download cannot start", () => {
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", {
      createObjectURL: () => "blob:fictional-fixture",
      revokeObjectURL,
    });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {
      throw new Error("Download blocked");
    });
    expect(() => downloadPublicFixture(initialConsole().records[0])).toThrow(
      "Download blocked",
    );
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:fictional-fixture");
  });
});
