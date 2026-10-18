import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import InvestigationPanel from "../app/passport/investigation-panel";
import InvestigationHistory from "../app/passport/investigation-history";
import { ApiError } from "../lib/api-client";
import type { InvestigationCommand } from "../lib/persona-investigation-contracts";
import { investigationResult } from "./investigation-fixtures";
import { preparedSource, version } from "./prepared-write-fixtures";
import { queryReceipt, similarityPage } from "./similarity-fixtures";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function source() {
  const value = preparedSource();
  value.investigations = {
    requestReview: vi.fn(),
    reviewRequests: vi.fn(async () => ({
      workspace_id: value.workspaceId,
      version_id: version.version_id,
      items: [],
      next_before_ordinal: null,
    })),
    workspaceId: value.workspaceId,
    readiness: vi.fn(async () => "ready" as const),
    generate: vi.fn(async (command: InvestigationCommand) =>
      investigationResult(command),
    ),
    history: vi.fn(async () => ({
      workspace_id: value.workspaceId,
      version_id: version.version_id,
      items: [investigationResult()],
      next_before_ordinal: null,
    })),
  };
  return value;
}
async function ready() {
  fireEvent.click(
    screen.getByRole("button", { name: "Check investigation availability" }),
  );
  await waitFor(() =>
    expect(
      (
        screen.getByRole("button", {
          name: "Check investigation availability",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false),
  );
  fireEvent.change(
    screen.getByLabelText("Where was this appearance supplied from?"),
    { target: { value: "Supplied frame" } },
  );
  fireEvent.click(screen.getByRole("checkbox"));
}
it("requires manual readiness, context and explicit retention before model calls; exposes gaps and review", async () => {
  const value = source(),
    page = similarityPage();
  render(
    <InvestigationPanel
      source={value}
      candidate={page.items[0]}
      receipt={queryReceipt()}
      page={page}
      denied={vi.fn()}
    />,
  );
  expect(value.investigations!.generate).not.toHaveBeenCalled();
  expect(
    (
      screen.getByRole("button", {
        name: "Generate grounded findings",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  await ready();
  fireEvent.click(
    screen.getByRole("button", { name: "Generate grounded findings" }),
  );
  await screen.findByText(/Pose differs between/);
  expect(
    screen.getByText(/Performer identity is not established/),
  ).toBeDefined();
  expect(screen.getByText("Prepare independent human review")).toBeDefined();
  expect(value.investigations!.generate).toHaveBeenCalledWith(
    expect.objectContaining({
      retain_findings: true,
      version_id: version.version_id,
      source_note: "Supplied frame",
    }),
    expect.any(AbortSignal),
  );
});
it("retries the same frozen analysis intent after a provider failure", async () => {
  const value = source(),
    page = similarityPage(),
    generate = value.investigations!.generate as ReturnType<typeof vi.fn>;
  generate.mockRejectedValueOnce(new ApiError("Unavailable", 503));
  render(
    <InvestigationPanel
      source={value}
      candidate={page.items[0]}
      receipt={queryReceipt()}
      page={page}
      denied={vi.fn()}
    />,
  );
  await ready();
  fireEvent.click(
    screen.getByRole("button", { name: "Generate grounded findings" }),
  );
  fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
  await screen.findByText(/Pose differs between/);
  expect(generate.mock.calls[1][0]).toEqual(generate.mock.calls[0][0]);
});
it.each([403, 410])(
  "invalidates the selected query on denial or expiry %s",
  async (status) => {
    const value = source(),
      page = similarityPage(),
      denied = vi.fn();
    value.investigations!.generate = vi
      .fn()
      .mockRejectedValue(new ApiError("Unavailable", status));
    render(
      <InvestigationPanel
        source={value}
        candidate={page.items[0]}
        receipt={queryReceipt()}
        page={page}
        denied={denied}
      />,
    );
    await ready();
    fireEvent.click(
      screen.getByRole("button", { name: "Generate grounded findings" }),
    );
    await waitFor(() => expect(denied).toHaveBeenCalled());
    expect(
      screen.queryByLabelText("Grounded investigation findings"),
    ).toBeNull();
  },
);
it("cancel ignores late findings and exposes saved exact-version history", async () => {
  const value = source(),
    page = similarityPage();
  let finish: (
    value: ReturnType<typeof investigationResult>,
  ) => void = () => {};
  value.investigations!.generate = vi.fn(
    () =>
      new Promise<ReturnType<typeof investigationResult>>((resolve) => {
        finish = resolve;
      }),
  );
  const view = render(
    <InvestigationPanel
      source={value}
      candidate={page.items[0]}
      receipt={queryReceipt()}
      page={page}
      denied={vi.fn()}
    />,
  );
  await ready();
  fireEvent.click(
    screen.getByRole("button", { name: "Generate grounded findings" }),
  );
  fireEvent.click(await screen.findByRole("button", { name: "Stop loading" }));
  await act(async () => finish(investigationResult()));
  expect(screen.queryByLabelText("Grounded investigation findings")).toBeNull();
  await screen.findByText(/Server processing may finish/);
  view.unmount();
  render(
    <InvestigationHistory source={value} version={version} denied={vi.fn()} />,
  );
  await screen.findByText(/Pose differs between/);
  expect(value.investigations!.history).toHaveBeenCalledWith(
    version.version_id,
    null,
    expect.any(AbortSignal),
  );
});
