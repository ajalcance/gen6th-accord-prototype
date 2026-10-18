// @vitest-environment node
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { describe, expect, it } from "vitest";

interface Ast {
  type: string;
  value?: string;
  nodes?: Ast[];
  invalid?: boolean;
}
interface Options {
  maxDepth?: unknown;
  escapeInvalid?: boolean;
  rangeLimit?: number;
}
interface Braces {
  parse(input: string, options?: Options): Ast;
  compile(input: string | Ast, options?: Options): string;
  expand(input: string | Ast, options?: Options): string[];
  stringify(input: string | Ast, options?: Options): string;
}
interface Manifest {
  name: string;
  version: string;
  scripts?: Record<string, string>;
  accordBackport: { release: string; patchSha256: string };
}
interface Lock {
  packages: Record<
    string,
    { version?: string; resolved?: string; integrity?: string }
  >;
}

interface AppManifest {
  devDependencies: Record<string, string>;
  overrides: Record<string, string | Record<string, string>>;
}

const requireDependency = createRequire(import.meta.url);
const appRoot = process.cwd();
const appName = path.basename(appRoot);
const repository = path.dirname(appRoot);
const source = path.join(repository, "vendor/braces/source");
const artifact = "vendor/braces/braces-3.0.4-accord.1.tgz";
const archiveHash =
  "2155cb703acd5f4247164321feb72df40214676b5cc7c362060f56e64e33bf7c";
const patchHash =
  "54633452e16239fe127f90c12cfecf14939396d562b095f9a16ba753eea1bff4";
const approvedPatchHash =
  "a3f08706e45f1e180112f91f07a871b284b92613bccdfb2724a165ff4f96c91e";
const integrity =
  "sha512-mq+bKmdbUUTDiQZqhfUAA4DnYOW5iAhcXBq7VtQ8SD4rvfSsvL5gEwWMJ4o8YNSWNlRW6toXlKNhFDHaBP0Oaw==";
const mmRequire = createRequire(requireDependency.resolve("micromatch"));
const installed = path.dirname(mmRequire.resolve("braces/package.json"));
const braces = mmRequire("braces") as Braces;
const methods = ["compile", "expand", "stringify"] as const;

function json<T>(file: string): T {
  return JSON.parse(readFileSync(file, "utf8")) as T;
}
function digest(file: string): string {
  return createHash("sha256").update(readFileSync(file)).digest("hex");
}
function nested(depth: number, open = "{", close = "}"): string {
  return open.repeat(depth) + "a" + close.repeat(depth);
}
function ast(depth: number, type = "brace"): Ast {
  let node: Ast = { type: "text", value: "a" };
  for (let i = 0; i < depth; i++) node = { type, nodes: [node] };
  return { type: "root", nodes: [node] };
}

describe("the installed private braces correction", () => {
  it("pins the reviewed archive and source patch in each build context", () => {
    expect(digest(path.join(appRoot, artifact))).toBe(archiveHash);
    expect(
      digest(path.join(repository, "vendor/braces/braces-3.0.4-accord.1.tgz")),
    ).toBe(archiveHash);
    expect(
      digest(path.join(repository, "vendor/braces/depth-backport.patch")),
    ).toBe(patchHash);
    const manifest = json<Manifest>(path.join(installed, "package.json"));
    expect(manifest.name).toBe("braces");
    expect(manifest.version).toBe("3.0.4-accord.1");
    expect(manifest.scripts).toBeUndefined();
    expect(manifest.accordBackport.release).toBe("3.0.3");
    expect(manifest.accordBackport.patchSha256).toBe(approvedPatchHash);
    const rootManifest = json<AppManifest>(path.join(appRoot, "package.json"));
    expect(rootManifest.devDependencies.braces).toBe("file:" + artifact);
    expect(rootManifest.overrides["micromatch@4.0.8"]).toEqual({
      braces: "3.0.4-accord.1",
    });
    const lock = json<Lock>(path.join(appRoot, "package-lock.json"));
    expect(lock.packages["node_modules/braces"]).toMatchObject({
      version: "3.0.4-accord.1",
      resolved: "file:" + artifact,
      integrity,
    });
  });

  it("installs exactly the reviewed source, license and provenance", () => {
    const files = [
      "index.js",
      "package.json",
      "LICENSE",
      "UPSTREAM.md",
      ...["constants", "utils", "parse", "compile", "expand", "stringify"].map(
        (name) => "lib/" + name + ".js",
      ),
    ];
    for (const file of files) {
      expect(readFileSync(path.join(installed, file))).toEqual(
        readFileSync(path.join(source, file)),
      );
    }
  });

  it.each(["{", "("])("accepts 100 levels and rejects 101 for %s", (open) => {
    const close = open === "{" ? "}" : ")";
    for (const method of ["parse", ...methods] as const) {
      expect(() => braces[method](nested(100, open, close))).not.toThrow();
      expect(() => braces[method](nested(101, open, close))).toThrow(
        /Input depth .* exceeds max depth/,
      );
    }
  });

  it.each([undefined, 1e9, Infinity, NaN, "untrusted"])(
    "cannot widen the string depth limit with %s",
    (maxDepth) => {
      for (const method of ["parse", ...methods] as const) {
        expect(() => braces[method](nested(4000), { maxDepth })).toThrow(
          /Input depth .* exceeds max depth/,
        );
      }
    },
  );

  it.each(methods)("bounds %s for a directly supplied deep AST", (method) => {
    for (const type of ["brace", "paren"]) {
      expect(() => braces[method](ast(100, type))).not.toThrow();
      for (const depth of [101, 1000, 10000]) {
        expect(() =>
          braces[method](ast(depth, type), { maxDepth: 1e9 }),
        ).toThrow(/AST depth .* exceeds max depth/);
      }
    }
  });

  it.each([0, 0.5, 1, 1.5, 2, -1])(
    "normalizes stricter depth %s consistently",
    (maxDepth) => {
      const accepted = Math.max(0, Math.floor(maxDepth));
      for (const method of ["parse", ...methods] as const) {
        expect(() =>
          braces[method](nested(accepted), { maxDepth }),
        ).not.toThrow();
        expect(() =>
          braces[method](nested(accepted + 1), { maxDepth }),
        ).toThrow(/Input depth .* exceeds max depth/);
      }
      for (const method of methods) {
        expect(() => braces[method](ast(accepted), { maxDepth })).not.toThrow();
        expect(() => braces[method](ast(accepted + 1), { maxDepth })).toThrow(
          /AST depth .* exceeds max depth/,
        );
      }
    },
  );

  it("preserves published expansion, invalid escaping, quoting and AST shape", () => {
    expect(braces.expand("{a,{b,c}}")).toEqual(["a", "b", "c"]);
    expect(braces.expand("{01..03}")).toEqual(["01", "02", "03"]);
    expect(braces.stringify("{{a}}", { escapeInvalid: true })).toBe("{{a}}");
    expect(braces.stringify(nested(100))).toBe(nested(100));
    expect(braces.stringify('"' + "{".repeat(1000) + '"')).toBe(
      "{".repeat(1000),
    );
    expect(() => braces.parse("\\{".repeat(1000))).not.toThrow();
    expect(
      braces.parse("{a,b}").nodes?.find((node) => node.type === "brace"),
    ).not.toHaveProperty("invalid");
    expect(() => braces.expand("{1..100}", { rangeLimit: 2 })).toThrow(
      /range limit/,
    );
  });

  it("the real micromatch, fast-glob and Next lint resolver use the corrected package", () => {
    expect(mmRequire.resolve("braces")).toBe(path.join(installed, "index.js"));
    const mm = requireDependency("micromatch") as {
      braces(pattern: string, options: { expand: boolean }): string[];
    };
    const fg = requireDependency("fast-glob") as {
      globSync(
        pattern: string,
        options: { onlyDirectories: boolean },
      ): string[];
    };
    const next = requireDependency(
      "@next/eslint-plugin-next/dist/utils/get-root-dirs",
    ) as {
      getRootDirs(context: {
        cwd: string;
        settings: { next: { rootDir: string } };
      }): string[];
    };
    expect(mm.braces("{app,tests}", { expand: true })).toEqual([
      "app",
      "tests",
    ]);
    const pattern = appRoot + "/{app,tests}";
    const expected = [
      path.join(appRoot, "app"),
      path.join(appRoot, "tests"),
    ].sort();
    expect(fg.globSync(pattern, { onlyDirectories: true }).sort()).toEqual(
      expected,
    );
    expect(
      next
        .getRootDirs({ cwd: appRoot, settings: { next: { rootDir: pattern } } })
        .sort(),
    ).toEqual(expected);
    const hostile = "{".repeat(101) + appName + ",app" + "}".repeat(101);
    expect(() => mm.braces(hostile, { expand: true })).toThrow(
      /exceeds max depth/,
    );
    expect(() => fg.globSync(hostile, { onlyDirectories: true })).toThrow(
      /exceeds max depth/,
    );
    expect(() =>
      next.getRootDirs({
        cwd: appRoot,
        settings: { next: { rootDir: hostile } },
      }),
    ).toThrow(/exceeds max depth/);
  });
});
