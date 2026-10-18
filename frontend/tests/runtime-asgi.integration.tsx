/** Actual private FastAPI -> gateway -> React queue intent; synthetic services, no SQL/cloud. */
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import DurableFaceJobs from "../app/passport/durable-face-jobs";
import { runtimeGateway } from "../lib/persona-runtime";
import { capture } from "./capture-fixtures";
import { installBridge } from "./governance-asgi-helper";
import {
  draftProvider,
  preparedSource,
  version,
} from "./prepared-write-fixtures";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("shows configured delivery and queues exact approved references through actual ASGI", async () => {
  const bridge = installBridge(() => "ready", "runtime_bridge"),
    source = preparedSource();
  source.runtime = runtimeGateway(source.workspaceId);
  render(
    draftProvider(
      new Map(),
      <DurableFaceJobs
        source={source}
        version={version}
        capture={capture}
        result={null}
        reloadResult={vi.fn()}
        denied={vi.fn()}
      />,
    ),
  );
  const queue = await screen.findByRole(
    "button",
    { name: "Queue face detection" },
    { timeout: 10000 },
  );
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(queue);
  await screen.findByRole(
    "button",
    { name: "Reload saved jobs" },
    { timeout: 10000 },
  );
  expect(bridge.calls.map((call) => call.path.split("/").at(-1))).toEqual([
    "readiness",
    "history",
    "enqueue",
  ]);
  expect(bridge.calls[2].body).toEqual(
    expect.objectContaining({
      version_id: version.version_id,
      portrait_id: capture.portrait_id,
      generation_id: null,
      face_index: null,
    }),
  );
  expect(bridge.calls[2].body).not.toHaveProperty("actor_ref");
}, 15000);
it("clears available processing when the actual session boundary rejects a connection", async () => {
  const bridge = installBridge(() => "session_lost", "runtime_bridge"),
    source = preparedSource();
  source.runtime = runtimeGateway(source.workspaceId);
  render(
    <DurableFaceJobs
      source={source}
      version={version}
      capture={capture}
      result={null}
      reloadResult={vi.fn()}
      denied={vi.fn()}
    />,
  );
  await waitFor(() => expect(bridge.calls).toHaveLength(1));
  await screen.findByText(
    /session|sign in|connection/i,
    {},
    { timeout: 10000 },
  );
  expect(
    screen.queryByRole("button", { name: "Queue face detection" }),
  ).toBeNull();
});
