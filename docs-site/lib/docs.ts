import fs from "node:fs";
import path from "node:path";

// Publish ONLY docs/public/ — an allowlist, not a denylist. Everything else
// under docs/ (architecture, decisions, requirements, standards) is internal,
// and a new internal file must never become public by default.
// tests/published-docs.test.ts and tests/loader-boundary.test.ts hold this in CI.
const DOCS_DIR = path.join(process.cwd(), "..", "docs", "public");

export type DocMeta = { slug: string[]; title: string };

function isInside(root: string, file: string): boolean {
  const rel = path.relative(root, file);
  return rel !== "" && !path.isAbsolute(rel) && rel.split(path.sep)[0] !== "..";
}

// A slug segment is one plain name: never empty, ".", "..", or a path.
function isPlainName(segment: string): boolean {
  return (
    segment !== "" &&
    segment !== "." &&
    segment !== ".." &&
    !/[\\/\0]/.test(segment)
  );
}

// Symlinks are never followed: one could point anywhere on the machine that
// builds the site. Only real directories and regular .md files are published.
export function listDocs(): DocMeta[] {
  const out: DocMeta[] = [];
  const walk = (dir: string, prefix: string[]): void => {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        walk(path.join(dir, entry.name), [...prefix, entry.name]);
      } else if (entry.isFile() && entry.name.endsWith(".md")) {
        const slug = [...prefix, entry.name.replace(/\.md$/, "")];
        out.push({ slug, title: slug.join(" / ") });
      }
    }
  };
  walk(DOCS_DIR, []);
  return out.sort((a, b) => a.slug.join("/").localeCompare(b.slug.join("/")));
}

// The file a slug publishes, or null unless it is a regular file whose real
// path is inside docs/public/: a "..", a path segment, or a symlink anywhere on
// the way out of the root is refused, not followed.
export function resolveDoc(slug: string[]): string | null {
  if (!slug.every(isPlainName)) return null;
  const file = path.join(DOCS_DIR, ...slug) + ".md";
  if (!fs.lstatSync(file, { throwIfNoEntry: false })?.isFile()) return null;
  const inside = isInside(fs.realpathSync(DOCS_DIR), fs.realpathSync(file));
  return inside ? file : null;
}

export function readDoc(slug: string[]): string | null {
  if (resolveDoc(slug) === null) return null;
  // Kept as a path.join under DOCS_DIR so the bundler can see statically that
  // only docs/public/ is read. A computed path makes it trace, and ship, the
  // whole project with the server build.
  return fs.readFileSync(path.join(DOCS_DIR, ...slug) + ".md", "utf8");
}
