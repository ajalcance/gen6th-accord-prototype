/** Explicit two-runtime test bridge. No listener, real credentials, SQL or application mounting. */
import { execFile } from "node:child_process";
import { resolve } from "node:path";
import { vi } from "vitest";
import type { BridgeCall } from "./governance-asgi-helper";

type ResponseWire = {
  status: number;
  headers: Record<string, string>;
  body: unknown;
};
export function installWriteBridge(
  mode: (path: string, attempt: number) => string = () => "ready",
) {
  const calls: BridgeCall[] = [];
  const fetch = vi.fn<typeof globalThis.fetch>(async (input, options) => {
    const path = String(input),
      body = JSON.parse(String(options?.body)) as Record<string, unknown>;
    calls.push({ path, body, options: options ?? {} });
    const attempt = calls.filter((call) => call.path === path).length;
    const result = await runBridge({
      workspace: path.split("/")[3],
      path: path.split("/personas")[1],
      body,
      mode: mode(path, attempt),
      actor: path.endsWith("/reviews/record")
        ? "reviewer-a"
        : path.endsWith("/campaigns/decide") && body.decision !== "revoked"
          ? "recipient-a"
          : "creator-a",
    });
    return new Response(JSON.stringify(result.body), {
      status: result.status,
      headers: result.headers,
    });
  });
  vi.stubGlobal("fetch", fetch);
  return { calls, fetch };
}
function runBridge(command: unknown): Promise<ResponseWire> {
  const backend = resolve(process.cwd(), "../backend");
  return new Promise((done, reject) => {
    const child = execFile(
      resolve(backend, ".venv/bin/python"),
      ["-m", "personas.write_bridge"],
      {
        cwd: backend,
        env: {
          NODE_ENV: "test",
          PYTHONPATH: backend + ":" + resolve(backend, "tests"),
        },
        encoding: "utf8",
        timeout: 10000,
      },
      (error, output) => {
        if (error) reject(error);
        else done(JSON.parse(output) as ResponseWire);
      },
    );
    child.stdin?.end(JSON.stringify(command));
  });
}
