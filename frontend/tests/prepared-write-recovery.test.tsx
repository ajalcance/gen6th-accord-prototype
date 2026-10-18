import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api-client";
import type { PersonaTransport } from "../lib/persona-gateway";
import { personaGateway } from "../lib/persona-gateway";
import type { WriteDraftStore } from "../app/passport/prepared-write-state";
import SavedRecord from "../app/passport/saved-record";
import PassportStudio from "../app/passport/studio";
import {
  draftProvider,
  mountPrepared,
  preparedSource,
  receipt,
  version,
} from "./prepared-write-fixtures";

afterEach(() => {
  cleanup();
  localStorage.clear();
});
function fillSave() {
  for (const [label, value] of [
    ["Saved draft name", "Keep my local draft"],
    ["Saved draft biography", "My own text."],
    ["Saved draft contribution", "Human concept."],
    ["Saved draft AI disclosure", "Fictional fixture."],
  ]) {
    fireEvent.change(screen.getByLabelText(label), { target: { value } });
  }
  fireEvent.click(screen.getByRole("checkbox", { name: /I have reviewed/ }));
}

it("compares the new head after conflict, preserves draft text and requires a new explicit intent", async () => {
  const write = vi
    .fn<PersonaTransport>()
    .mockRejectedValueOnce(new ApiError("conflict", 409))
    .mockImplementation(async (operation, _workspace, body) =>
      receipt(operation, body),
    );
  const source = preparedSource(write);
  source.gateway = personaGateway(version.workspace_id, async () => ({
    ...version,
    revision: 2,
    content: { ...version.content, name: "Latest server name" },
  }));
  mountPrepared(source);
  fillSave();
  fireEvent.click(screen.getByRole("button", { name: "Save version" }));
  await screen.findByText(/server record changed/);
  expect(
    screen.queryByRole("button", { name: "Retry same intent" }),
  ).toBeNull();
  fireEvent.click(
    screen.getByRole("button", { name: "Compare latest saved version" }),
  );
  await screen.findByRole("heading", { name: "Latest saved version" });
  expect(screen.getByText("Latest server name")).toBeDefined();
  fireEvent.click(
    screen.getByRole("button", { name: "Use this version for a new intent" }),
  );
  expect(
    (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
  ).toBe("Keep my local draft");
  const save = screen.getByRole("button", {
    name: "Save version",
  }) as HTMLButtonElement;
  expect(save.disabled).toBe(true);
  fireEvent.click(screen.getByRole("checkbox", { name: /I have reviewed/ }));
  fireEvent.click(save);
  await screen.findByText(/Storage receipt validated/);
  expect(write.mock.calls[0][2]).toMatchObject({ expected_revision: 1 });
  expect(write.mock.calls[1][2]).toMatchObject({ expected_revision: 2 });
  expect(
    (write.mock.calls[0][2] as { request_id: string }).request_id,
  ).not.toBe((write.mock.calls[1][2] as { request_id: string }).request_id);
});

it("cancels pending UI immediately and ignores a late receipt after a same-intent retry", async () => {
  let finish: (result: unknown) => void = () => {};
  const write = vi
    .fn<PersonaTransport>()
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    )
    .mockImplementation(async (operation, _workspace, body) =>
      receipt(operation, body),
    );
  mountPrepared(preparedSource(write));
  fillSave();
  fireEvent.click(screen.getByRole("button", { name: "Save version" }));
  expect(screen.getByText(/Waiting for the server receipt/)).toBeDefined();
  fireEvent.click(screen.getByRole("button", { name: "Stop waiting" }));
  expect(screen.getByText(/Stopped waiting/)).toBeDefined();
  fireEvent.click(screen.getByRole("button", { name: "Retry same intent" }));
  await screen.findByText(/Storage receipt validated/);
  await act(async () => {
    finish(receipt("save", write.mock.calls[0][2]));
  });
  expect(screen.getByText(/Storage receipt validated/)).toBeDefined();
  expect(write.mock.calls[0][2]).toEqual(write.mock.calls[1][2]);
});

it.each([401, 403])(
  "clears fetched content after %s while retaining only the authored draft and failed intent",
  async (status) => {
    const store: WriteDraftStore = new Map(),
      source = preparedSource(async () => {
        throw new ApiError("private detail", status);
      });
    render(
      draftProvider(
        store,
        <SavedRecord
          source={source}
          personaId={version.persona_id}
          close={() => {}}
        />,
      ),
    );
    await screen.findByRole("button", { name: "Edit persona" });
    fireEvent.click(screen.getByRole("button", { name: "Edit persona" }));
    fillSave();
    fireEvent.click(screen.getByRole("button", { name: "Save version" }));
    await screen.findByText(/saved view was cleared/);
    expect(screen.queryByText(version.content.biography)).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Retry same intent" }),
    ).toBeNull();
    const entry = [...store.values()][0];
    expect(entry.fields.name).toBe("Keep my local draft");
    expect(entry.checkpoint?.state.phase).toBe("denied");
    expect(entry).not.toHaveProperty("receipt");
  },
);

it("keeps authored drafts across navigation and source loss, and hides them from another session", async () => {
  const source = preparedSource(),
    mounted = render(<PassportStudio savedSource={source} />);
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  fireEvent.click(await screen.findByRole("button", { name: "Edit persona" }));
  fillSave();
  mounted.rerender(<PassportStudio savedSource={null} />);
  expect(screen.queryByLabelText("Saved draft name")).toBeNull();
  mounted.rerender(<PassportStudio savedSource={source} />);
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  fireEvent.click(await screen.findByRole("button", { name: "Edit persona" }));
  expect(
    (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
  ).toBe("Keep my local draft");
  mounted.rerender(
    <PassportStudio
      savedSource={{ ...source, sessionKey: "different-synthetic-session" }}
    />,
  );
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  fireEvent.click(await screen.findByRole("button", { name: "Edit persona" }));
  expect(
    (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
  ).toBe(version.content.name);
});

it("ignores the previous session's late receipt and requires new confirmation after returning", async () => {
  let finish: (result: unknown) => void = () => {};
  const write = vi.fn<PersonaTransport>(
    async () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const source = preparedSource(write),
    mounted = mountPrepared(source);
  fillSave();
  fireEvent.click(screen.getByRole("button", { name: "Save version" }));
  mounted.rerender(
    mounted.element({ ...source, sessionKey: "new-synthetic-session" }),
  );
  await act(async () => {
    finish(receipt("save", write.mock.calls[0][2]));
  });
  expect(screen.queryByText(/Storage receipt validated/)).toBeNull();
  expect(
    (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
  ).toBe(version.content.name);
  mounted.rerender(mounted.element(source));
  expect(
    screen.getByRole("button", { name: "Retry same intent" }),
  ).toBeDefined();
  expect(
    (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
  ).toBe("Keep my local draft");
});
