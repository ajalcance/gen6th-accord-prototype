import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import RecordBrief from "../app/passport/record-brief";
import { ApiError } from "../lib/api-client";
import { parseBrief, type AssistantGateway } from "../lib/persona-assistant";
import { wireBrief } from "./assistant-fixtures";
import { preparedSource, version } from "./prepared-write-fixtures";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function mount(brief: AssistantGateway["brief"]) {
  const source = preparedSource();
  source.assistant = { workspaceId: source.workspaceId, brief };
  return {
    brief,
    ...render(<RecordBrief source={source} version={version} />),
  };
}
const ready = () => vi.fn(async () => parseBrief(wireBrief));

it("renders nothing without the optional capability", () => {
  const source = preparedSource();
  const { container } = render(<RecordBrief source={source} version={version} />);
  expect(container.innerHTML).toBe("");
});
it("sends nothing until the button is pressed, and says what will be sent", () => {
  const { brief } = mount(ready());
  expect(screen.getByText(/Google Gemini on Vertex AI/)).toBeTruthy();
  expect(screen.getByText(/human contribution and AI disclosure/)).toBeTruthy();
  expect(brief).not.toHaveBeenCalled();
});
it("shows the advisory draft, its gaps, questions, provenance and the fixed notice", async () => {
  const { brief } = mount(ready());
  fireEvent.click(screen.getByRole("button", { name: "Draft reviewer brief" }));
  await screen.findByText(wireBrief.summary);
  expect(screen.getByText(wireBrief.gaps[0])).toBeTruthy();
  expect(screen.getByText(wireBrief.questions[0])).toBeTruthy();
  expect(screen.getByText(wireBrief.notice)).toBeTruthy();
  expect(screen.getByText(/AI DRAFT · NOT A DECISION/)).toBeTruthy();
  expect(screen.getByText(/gemini-3.8-flash-001/)).toBeTruthy();
  expect(brief).toHaveBeenCalledWith(
    version.persona_id,
    version.revision,
    expect.any(AbortSignal),
  );
  expect(screen.getByRole("button", { name: "Draft again" })).toBeTruthy();
});
it("labels a thin record honestly instead of inventing a summary", async () => {
  mount(
    vi.fn(async () =>
      parseBrief({
        ...wireBrief,
        state: "insufficient_information",
        summary: "Too little text to summarise.",
        gaps: [],
        questions: [],
      }),
    ),
  );
  fireEvent.click(screen.getByRole("button", { name: "Draft reviewer brief" }));
  await screen.findByText("Too little text to summarise.");
  expect(screen.getByText(/NOT ENOUGH TEXT TO SUMMARISE/)).toBeTruthy();
  expect(screen.queryByText(/Questions to ask the creator/)).toBeNull();
});
it.each([
  ["rate limited", new ApiError("429", 429)],
  ["unavailable", new ApiError("503", 503)],
  ["network", new Error("offline")],
])("shows a plain failure and no brief when %s", async (_name, failure) => {
  mount(vi.fn(async () => Promise.reject(failure)));
  fireEvent.click(screen.getByRole("button", { name: "Draft reviewer brief" }));
  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toMatch(/could not be drafted right now/);
  expect(screen.queryByText(wireBrief.summary)).toBeNull();
  expect(
    (screen.getByRole("button", { name: "Draft reviewer brief" }) as HTMLButtonElement)
      .disabled,
  ).toBe(false);
});
it("never shows a brief that does not match the displayed version", async () => {
  mount(
    vi.fn(async () =>
      parseBrief({ ...wireBrief, version_id: crypto.randomUUID() }),
    ),
  );
  fireEvent.click(screen.getByRole("button", { name: "Draft reviewer brief" }));
  await waitFor(() =>
    expect(
      (screen.getByRole("button", { name: /Draft/ }) as HTMLButtonElement)
        .disabled,
    ).toBe(false),
  );
  expect(screen.queryByText(wireBrief.summary)).toBeNull();
});
it("disables the button while drafting so one click makes one request", async () => {
  let release: (value: ReturnType<typeof parseBrief>) => void = () => {};
  const { brief } = mount(
    vi.fn(
      () =>
        new Promise<ReturnType<typeof parseBrief>>((resolve) => {
          release = resolve;
        }),
    ),
  );
  fireEvent.click(screen.getByRole("button", { name: "Draft reviewer brief" }));
  const busy = await screen.findByRole("button", { name: "Drafting…" });
  expect((busy as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(busy);
  release(parseBrief(wireBrief));
  await screen.findByText(wireBrief.summary);
  expect(brief).toHaveBeenCalledTimes(1);
});
