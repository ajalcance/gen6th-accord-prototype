import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PerformerLifecycle from "../app/passport/performer-lifecycle";
import LifecycleUse from "../app/passport/lifecycle-use";
import { useWriteDraft } from "../app/passport/prepared-write-state";
import { lifecycleGateway } from "../lib/persona-lifecycle";
import { ApiError } from "../lib/api-client";
import { GovernanceAccessLoss } from "../app/passport/saved-governance-read";
import {
  draftProvider,
  preparedSource,
  version,
} from "./prepared-write-fixtures";
import { lifecycleProfile, lifecycleReceipt, id } from "./lifecycle-fixtures";
import type { AppendLifecycle } from "../lib/persona-lifecycle-contracts";

afterEach(cleanup);

it("shows three missing assessments on an empty declared profile and does not fetch closed history", async () => {
  const transport = vi.fn().mockResolvedValue({
    ...lifecycleProfile,
    dossier: null,
    requirements: lifecycleProfile.requirements.map((item) => ({
      ...item,
      status: "missing",
      assessment: null,
    })),
  });
  mount(transport);
  await screen.findByText(
    "No lifecycle declaration recorded for this version.",
  );
  expect(screen.getAllByText("missing")).toHaveLength(3);
  expect(transport).toHaveBeenCalledTimes(1);
});
function mount(
  transport: (
    path: string,
    body: unknown,
    signal: AbortSignal,
  ) => Promise<unknown>,
  denied = vi.fn(),
) {
  const source = {
    ...preparedSource(),
    lifecycle: lifecycleGateway(version.workspace_id, transport),
  };
  return {
    source,
    denied,
    ...render(
      draftProvider(
        new Map(),
        <GovernanceAccessLoss.Provider value={denied}>
          <PerformerLifecycle
            source={source}
            version={version}
            denied={denied}
          />
        </GovernanceAccessLoss.Provider>,
      ),
    ),
  };
}
it("shows separate assessments and declared provenance without a blanket verified badge", async () => {
  mount(vi.fn().mockResolvedValue(lifecycleProfile));
  await screen.findByText("Fictional operator");
  expect(screen.getByText("Owner declared")).toBeTruthy();
  expect(screen.getAllByText("approved")).toHaveLength(3);
  expect(screen.queryByText("Verified performer")).toBeNull();
  expect(screen.getByText(/No active performer suspension/)).toBeTruthy();
});
it("requires deliberate concern confirmation and retries the same intent", async () => {
  const transport = vi.fn(async (path: string, body: unknown) => {
    if (path === "read") return lifecycleProfile;
    const command = body as AppendLifecycle;
    return {
      ...lifecycleReceipt,
      ...command,
      id: id(400),
      evidence_digests: {},
    };
  });
  mount(transport);
  await screen.findByText("Fictional operator");
  fireEvent.change(screen.getByLabelText("Concern details"), {
    target: { value: "Review this rights claim" },
  });
  const submit = screen.getByRole("button", { name: "Record concern" });
  expect(submit.hasAttribute("disabled")).toBe(true);
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I reviewed this concern/ }),
  );
  transport.mockRejectedValueOnce(new ApiError("Unavailable", 503));
  fireEvent.click(submit);
  fireEvent.click(
    await screen.findByRole("button", { name: "Retry same intent" }),
  );
  await screen.findByText(/Storage receipt validated/);
  const calls = transport.mock.calls.filter(([path]) => path === "append");
  expect(calls).toHaveLength(2);
  expect(calls[0][1]).toEqual(calls[1][1]);
});
it("read failures and access loss never appear as absent requirements", async () => {
  const transport = vi.fn().mockRejectedValue(new ApiError("Unavailable", 503));
  const { denied } = mount(transport);
  await screen.findByRole("alert");
  expect(screen.queryByText(/No lifecycle declaration/)).toBeNull();
  transport.mockRejectedValue(new ApiError("Denied", 403));
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  await waitFor(() => expect(denied).toHaveBeenCalledOnce());
});
it("reports suspension and keeps resolved cases free of response controls", async () => {
  const report = {
    ...lifecycleReceipt,
    id: id(410),
    content: {
      kind: "concern",
      category: "rights",
      statement: "Synthetic report",
    },
    evidence_digests: {},
  };
  const response = {
    ...lifecycleReceipt,
    id: id(411),
    actor_ref: "reviewer",
    content: {
      kind: "response",
      concern_id: report.id,
      decision: "resolved",
      statement: "Synthetic resolution",
    },
    evidence_digests: {},
  };
  mount(
    vi.fn().mockResolvedValue({
      ...lifecycleProfile,
      suspended: true,
      concerns: [{ report, response }],
    }),
  );
  await screen.findByText(/Performer suspended:/);
  expect(screen.queryByText("Independent reviewer response")).toBeNull();
});
it("binding records operator and dossier together and trial selects private distribution", async () => {
  const source = {
    ...preparedSource(),
    lifecycle: lifecycleGateway(
      version.workspace_id,
      vi.fn().mockResolvedValue(lifecycleProfile),
    ),
  };
  function Harness() {
    const draft = useWriteDraft("binding", {});
    return (
      <>
        <LifecycleUse
          source={source}
          versionId={version.version_id}
          draft={draft}
        />
        <output data-testid="draft">{JSON.stringify(draft.fields)}</output>
      </>
    );
  }
  render(<Harness />);
  fireEvent.click(screen.getByRole("checkbox", { name: /Bind reviewed/ }));
  fireEvent.click(
    await screen.findByRole("button", {
      name: "Use this reviewed declaration",
    }),
  );
  expect(JSON.parse(screen.getByTestId("draft").textContent!)).toMatchObject({
    lifecycleProfile: lifecycleReceipt.id,
    lifecycleOperator: "operator",
  });
  fireEvent.change(screen.getByLabelText("Use mode"), {
    target: { value: "trial" },
  });
  expect(JSON.parse(screen.getByTestId("draft").textContent!)).toMatchObject({
    useMode: "trial",
    distribution: "private",
  });
  expect(screen.getByLabelText("Distribution").hasAttribute("disabled")).toBe(
    true,
  );
});
