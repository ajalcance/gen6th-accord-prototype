/** Test-only process bridge: actual FastAPI serialization, no listener, SQL or live identity. */
import { execFile } from "node:child_process";
import { resolve } from "node:path";
import { vi } from "vitest";

type WireResponse = {
  status: number;
  headers: Record<string, string>;
  body: unknown;
};
export type BridgeCall = {
  path: string;
  body: Record<string, unknown>;
  options: RequestInit;
};
export function installBridge(
  mode: (path: string) => string = () => "ready",
  module: "governance_bridge" | "runtime_bridge" = "governance_bridge",
) {
  const calls: BridgeCall[] = [];
  const fetch = vi.fn<typeof globalThis.fetch>(async (input, options) => {
    const path = String(input),
      body = JSON.parse(String(options?.body)) as Record<string, unknown>;
    calls.push({ path, body, options: options ?? {} });
    const workspace = path.split("/")[3];
    const result = await runBridge(
      {
        workspace,
        path: path.split("/personas")[1],
        body,
        mode: mode(path),
      },
      module,
    );
    return new Response(JSON.stringify(result.body), {
      status: result.status,
      headers: result.headers,
    });
  });
  vi.stubGlobal("fetch", fetch);
  return { calls, fetch };
}

function runBridge(
  command: unknown,
  module: "governance_bridge" | "runtime_bridge",
): Promise<WireResponse> {
  const backend = resolve(process.cwd(), "../backend");
  return new Promise((done, reject) => {
    const child = execFile(
      resolve(backend, ".venv/bin/python"),
      ["-m", `personas.${module}`],
      {
        cwd: backend,
        env: {
          NODE_ENV: "test",
          PYTHONPATH: `${backend}:${resolve(backend, "tests")}`,
        },
        encoding: "utf8",
        timeout: 10000,
      },
      (error, output) => {
        if (error) reject(error);
        else done(JSON.parse(output) as WireResponse);
      },
    );
    child.stdin?.end(JSON.stringify(command));
  });
}
