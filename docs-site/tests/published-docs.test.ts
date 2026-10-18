// The public-only rule, proven against the REAL repository and the REAL loader (TA-011).
//
// docs-site publishes docs/public/ and nothing else; everything else under docs/ is internal
// (architecture, ADRs, requirements, standards). Until this file existed the only proof was the
// `next build` route list, which a reviewer had to read. These tests fail the merge instead.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { listDocs, readDoc, resolveDoc } from "../lib/docs";

// Located from this file, never from process.cwd(): the loader derives its root from the
// working directory, and an oracle sharing that assumption would agree with any mistake in it.
const SITE_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
const DOCS_ROOT = fs.realpathSync(path.join(SITE_DIR, "..", "docs"));
const PUBLIC_ROOT = fs.realpathSync(path.join(DOCS_ROOT, "public"));

function isInside(root: string, file: string): boolean {
  const rel = path.relative(root, file);
  return rel !== "" && !path.isAbsolute(rel) && rel.split(path.sep)[0] !== "..";
}

// Every Markdown file under a directory, as real paths. Deliberately a different walk from the
// loader's, so the two can disagree.
function markdownUnder(dir: string): string[] {
  return fs
    .readdirSync(dir, { recursive: true, encoding: "utf8" })
    .filter((rel) => rel.endsWith(".md"))
    .map((rel) => fs.realpathSync(path.join(dir, rel)))
    .sort();
}

// What the site would publish, as real paths so a symlink cannot hide where a file lives.
function publishedFiles(): string[] {
  return listDocs()
    .map((doc) => resolveDoc(doc.slug))
    .filter((file): file is string => file !== null)
    .map((file) => fs.realpathSync(file))
    .sort();
}

describe("the docs site publishes docs/public/ and nothing else", () => {
  it("runs from the docs-site directory, where `next build` runs", () => {
    // The loader resolves docs/public/ from the working directory. Anywhere else, every
    // assertion below would describe some other tree.
    expect(fs.realpathSync(process.cwd())).toBe(fs.realpathSync(SITE_DIR));
  });

  it("publishes at least one document (a check over an empty set passes forever)", () => {
    const docs = listDocs();
    console.info(
      `docs-site publishes ${docs.length} document(s) from ${PUBLIC_ROOT}`,
    );
    expect(docs.length).toBeGreaterThan(0);
  });

  it("resolves every published document to a file inside docs/public/", () => {
    const docs = listDocs();
    expect(docs.length).toBeGreaterThan(0);
    const outside = docs
      .map((doc) => ({ slug: doc.slug.join("/"), file: resolveDoc(doc.slug) }))
      .filter(
        ({ file }) =>
          file === null || !isInside(PUBLIC_ROOT, fs.realpathSync(file)),
      );
    expect(
      outside,
      "published slugs that do not resolve inside docs/public/",
    ).toEqual([]);
    for (const doc of docs) {
      const file = resolveDoc(doc.slug) as string;
      expect(readDoc(doc.slug)).toBe(fs.readFileSync(file, "utf8"));
    }
  });

  it("publishes every Markdown file in docs/public/", () => {
    const expected = markdownUnder(PUBLIC_ROOT);
    expect(expected.length).toBeGreaterThan(0);
    expect(publishedFiles()).toEqual(expected);
  });

  it("publishes no document from the rest of docs/", () => {
    const internal = markdownUnder(DOCS_ROOT).filter(
      (file) => !isInside(PUBLIC_ROOT, file),
    );
    console.info(
      `checked ${internal.length} internal document(s) under ${DOCS_ROOT}`,
    );
    // Without internal documents to check, this test would prove nothing.
    expect(internal.length).toBeGreaterThan(0);

    const published = new Set(publishedFiles());
    expect(internal.filter((file) => published.has(file))).toEqual([]);

    // Nor can one be reached by walking up out of docs/public/ with a crafted slug.
    const reachable = internal.filter((file) => {
      const slug = path
        .relative(PUBLIC_ROOT, file)
        .replace(/\.md$/, "")
        .split(path.sep);
      return readDoc(slug) !== null || resolveDoc(slug) !== null;
    });
    expect(
      reachable,
      "internal documents readable through a '..' slug",
    ).toEqual([]);
  });
});
