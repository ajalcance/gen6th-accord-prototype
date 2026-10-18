// The loader's boundary, proven on a fixture tree it has never seen (TA-011: the REAL
// lib/docs.ts, pointed at a temporary directory through the working directory it already reads —
// no test-only switch in production code).
//
// The real repository holds no symlink and no hostile slug, so published-docs.test.ts cannot show
// that the loader refuses them. This tree plants each escape and asserts both directions
// (TA-010): what must be published is, and what must not be is not.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

type DocsModule = typeof import("../lib/docs");

// Built from these lists and torn down from them in reverse — no recursive delete of a path
// assembled at runtime (SEC-012).
const DIRS = [
  "site",
  "bare",
  "site/docs-site",
  "site/docs",
  "site/docs/architecture",
  "site/docs/public",
  "site/docs/public/nested",
  "bare/docs-site",
  "bare/docs",
];
const FILES: Record<string, string> = {
  "site/docs/internal.md": "INTERNAL — must never be published",
  "site/docs/architecture/secret.md": "ARCHITECTURE — must never be published",
  "site/docs/public/guide.md": "PUBLIC GUIDE",
  "site/docs/public/nested/deep.md": "PUBLIC NESTED",
  "site/docs/public/notes.txt": "not Markdown, so not a page",
  "bare/docs/internal.md": "INTERNAL — docs/public/ does not exist here",
};
// A file link and a directory link pointing out of docs/public/, and one that stays inside.
const LINKS: Record<string, string> = {
  "site/docs/public/leak.md": "../internal.md",
  "site/docs/public/linked": "../architecture",
  "site/docs/public/alias.md": "guide.md",
};

let root = "";

async function loaderAt(siteDir: string): Promise<DocsModule> {
  vi.resetModules();
  const cwd = vi
    .spyOn(process, "cwd")
    .mockReturnValue(path.join(root, siteDir));
  try {
    return await import("../lib/docs");
  } finally {
    cwd.mockRestore();
  }
}

beforeAll(() => {
  root = fs.realpathSync(
    fs.mkdtempSync(path.join(os.tmpdir(), "docs-site-fixture-")),
  );
  for (const dir of DIRS) fs.mkdirSync(path.join(root, dir));
  for (const [file, body] of Object.entries(FILES))
    fs.writeFileSync(path.join(root, file), body);
  for (const [link, target] of Object.entries(LINKS))
    fs.symlinkSync(target, path.join(root, link));
});

afterAll(() => {
  if (!root) return;
  // unlink removes a link as itself, never through to its target (a directory, for one of them).
  for (const entry of [...Object.keys(LINKS), ...Object.keys(FILES)]) {
    const target = path.join(root, entry);
    if (fs.lstatSync(target, { throwIfNoEntry: false })) fs.unlinkSync(target);
  }
  for (const dir of [...DIRS].reverse()) {
    if (fs.existsSync(path.join(root, dir))) fs.rmdirSync(path.join(root, dir));
  }
  fs.rmdirSync(root);
});

describe("the loader's boundary", () => {
  it("publishes exactly the regular Markdown files inside docs/public/", async () => {
    const { listDocs } = await loaderAt("site/docs-site");
    expect(listDocs().map((doc) => doc.slug)).toEqual([
      ["guide"],
      ["nested", "deep"],
    ]);
  });

  it("serves a published document's own content", async () => {
    const { readDoc, resolveDoc } = await loaderAt("site/docs-site");
    expect(readDoc(["guide"])).toBe("PUBLIC GUIDE");
    expect(readDoc(["nested", "deep"])).toBe("PUBLIC NESTED");
    expect(resolveDoc(["guide"])).toBe(
      path.join(root, "site/docs/public/guide.md"),
    );
  });

  it("refuses a slug that walks out of docs/public/", async () => {
    const { readDoc, resolveDoc } = await loaderAt("site/docs-site");
    const hostile = [
      ["..", "internal"],
      ["..", "architecture", "secret"],
      ["nested", "..", "..", "internal"],
      [path.join(root, "site/docs/internal")],
    ];
    expect(hostile.map((slug) => readDoc(slug))).toEqual(
      hostile.map(() => null),
    );
    expect(hostile.map((slug) => resolveDoc(slug))).toEqual(
      hostile.map(() => null),
    );
  });

  it("does not follow a symlink out of docs/public/", async () => {
    const { listDocs, readDoc } = await loaderAt("site/docs-site");
    const slugs = listDocs().map((doc) => doc.slug.join("/"));
    expect(slugs).not.toContain("leak");
    expect(slugs).not.toContain("linked/secret");
    expect(readDoc(["leak"])).toBeNull();
    expect(readDoc(["linked", "secret"])).toBeNull();
  });

  it("serves a document only under the slug it is listed with", async () => {
    // readDoc must never serve more than listDocs publishes: no alias, no link, no path slug.
    const { listDocs, readDoc } = await loaderAt("site/docs-site");
    const listed = listDocs().map((doc) => doc.slug.join("/"));
    expect(listed).not.toContain("alias");
    expect(readDoc(["guide"])).toBe("PUBLIC GUIDE");
    const aliases = [
      ["alias"],
      ["nested/deep"],
      ["nested", "..", "guide"],
      ["nested", ".", "deep"],
      [],
    ];
    expect(aliases.map((slug) => readDoc(slug))).toEqual(
      aliases.map(() => null),
    );
  });

  it("publishes nothing when docs/public/ does not exist", async () => {
    const { listDocs, readDoc } = await loaderAt("bare/docs-site");
    expect(listDocs()).toEqual([]);
    expect(readDoc(["..", "internal"])).toBeNull();
  });
});
