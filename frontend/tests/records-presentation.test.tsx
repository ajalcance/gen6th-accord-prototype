import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PassportStudio from "../app/passport/studio";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import { preparedSource } from "./prepared-write-fixtures";
import { portraitGateway } from "./portrait-fixtures";
import wire from "./fixtures/persona-wire.json";

afterEach(cleanup);

it("places System Capture beside record tools and keeps one explicit search action", async () => {
  const read = vi.fn<PersonaTransport>(async (operation) =>
    operation === "gallery" ? wire.gallery : wire.version,
  );
  const source = preparedSource();
  source.gateway = personaGateway(source.workspaceId, read);
  source.photos = portraitGateway(source.workspaceId);
  render(<PassportStudio savedSource={source} />);
  const card = await screen.findByRole("button", { name: /Open record/ });
  expect(
    await within(card).findByText("Incomplete — portrait required"),
  ).toBeDefined();
  const tools = screen.getByLabelText("Record tools");
  expect(within(tools).getByText("1 record")).toBeDefined();
  expect(within(tools).getAllByRole("searchbox")).toHaveLength(1);
  expect(
    within(tools).getAllByRole("button", { name: "Search records" }),
  ).toHaveLength(1);
  expect(
    within(tools).getByRole("button", { name: "New capture" }),
  ).toBeDefined();
  expect(
    within(screen.getByRole("banner")).queryByRole("button", {
      name: "New capture",
    }),
  ).toBeNull();
  expect(within(card).getByText(wire.version.content.biography)).toBeDefined();
  expect(within(card).getByText("Saved record")).toBeDefined();
  expect(within(card).getByText("Open record")).toBeDefined();
  expect(card.querySelector("time")?.getAttribute("datetime")).toBe(
    wire.version.recorded_at,
  );
  expect(card.querySelector("img")).toBeNull();
  fireEvent.change(screen.getByRole("searchbox"), {
    target: { value: "Fictional" },
  });
  expect(read).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Search records" }));
  await screen.findByRole("button", { name: /Open record/ });
  expect(read).toHaveBeenCalledTimes(2);
  fireEvent.click(screen.getByRole("button", { name: "New capture" }));
  expect(screen.getByRole("form", { name: "System Capture" })).toBeDefined();
});

it("opens a prefilled editor directly and retains authored edits across pane changes", async () => {
  const source = preparedSource();
  source.gateway = personaGateway(source.workspaceId, async (operation) =>
    operation === "gallery" ? wire.gallery : wire.version,
  );
  render(<PassportStudio savedSource={source} />);
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  fireEvent.click(await screen.findByRole("button", { name: "Edit persona" }));
  for (const [label, value] of [
    ["Saved draft name", wire.version.content.name],
    ["Saved draft biography", wire.version.content.biography],
    ["Saved draft contribution", wire.version.content.human_contribution],
    ["Saved draft AI disclosure", wire.version.content.ai_disclosure],
  ]) {
    expect((screen.getByLabelText(label) as HTMLInputElement).value).toBe(
      value,
    );
  }
  expect(
    (screen.getByRole("button", { name: "Save version" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  fireEvent.change(screen.getByLabelText("Saved draft name"), {
    target: { value: "My unsaved edit" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Activity" }));
  fireEvent.click(screen.getByRole("button", { name: "Overview" }));
  fireEvent.click(screen.getByRole("button", { name: "Edit persona" }));
  expect(
    (screen.getByLabelText("Saved draft name") as HTMLInputElement).value,
  ).toBe("My unsaved edit");
  const receipt = screen
    .getByText("Inspect storage receipt")
    .closest("details")!;
  expect(within(receipt).getByText("Record ID")).toBeDefined();
  expect(within(receipt).getByText(wire.version.persona_id)).toBeDefined();
});
