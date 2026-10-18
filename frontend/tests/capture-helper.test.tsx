import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PassportStudio from "../app/passport/studio";
import { preparedSource } from "./prepared-write-fixtures";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function start() {
  render(<PassportStudio />);
  fireEvent.click(screen.getByRole("button", { name: "New capture" }));
}
function helper() {
  fireEvent.click(screen.getByRole("button", { name: /Capture helper/ }));
  return screen.getByRole("region", { name: "Capture helper" });
}
it("opens only the name initially, replaces the wide panel and guides the next incomplete field", () => {
  start();
  expect(screen.getByLabelText("Persona name").closest("details")?.open).toBe(
    true,
  );
  for (const [label, hint] of [
    ["Persona name", "Name this persona record."],
    ["Biography", "Describe the persona and its intended context."],
    [
      "Human contribution",
      "Describe the human work, such as writing, direction or illustration.",
    ],
    ["AI disclosure", "Describe any AI use, or state that none was used."],
  ]) {
    expect(screen.getAllByText(label)).toHaveLength(1);
    expect(screen.getByLabelText(label).getAttribute("placeholder")).toBe(hint);
    expect(screen.queryByText(hint)).toBeNull();
  }
  expect(
    screen.queryByText("Upload this AI persona's face image to register it."),
  ).toBeNull();
  expect(
    screen.getAllByText(
      "Choose a portrait or an image that represents this persona.",
    ),
  ).toHaveLength(1);
  expect(screen.getByLabelText("Biography").closest("details")?.open).toBe(
    false,
  );
  expect(screen.queryByText(/of 4 details entered/)).toBeNull();
  expect(screen.queryByRole("region", { name: "Capture helper" })).toBeNull();
  fireEvent.change(screen.getByLabelText("Persona name"), {
    target: { value: "Performer" },
  });
  const panel = helper();
  fireEvent.click(
    within(panel).getByRole("button", { name: "Next: Biography" }),
  );
  expect(screen.queryByRole("region", { name: "Capture helper" })).toBeNull();
  expect(document.activeElement).toBe(screen.getByLabelText("Biography"));
  expect(screen.getByLabelText("Biography").closest("details")?.open).toBe(
    true,
  );
});
it("opens invalid required fields, counts overlong data as incomplete and restores focus on Escape", () => {
  start();
  fireEvent.invalid(screen.getByLabelText("AI disclosure"));
  expect(screen.getByLabelText("AI disclosure").closest("details")?.open).toBe(
    true,
  );
  fireEvent.change(screen.getByLabelText("Persona name"), {
    target: { value: "a".repeat(81) },
  });
  const panel = helper();
  expect(
    within(panel).getByRole("button", { name: "Next: Persona name" }),
  ).toBeDefined();
  fireEvent.keyDown(panel, { key: "Escape" });
  expect(document.activeElement).toBe(
    screen.getByRole("button", { name: /Capture helper/ }),
  );
  expect(screen.queryByRole("region", { name: "Capture helper" })).toBeNull();
});
it("jumps to portrait selection without uploading or saving and puts guidance behind a disclosure", () => {
  const write = vi.fn(),
    source = preparedSource(write);
  render(<PassportStudio savedSource={source} />);
  fireEvent.click(screen.getByRole("button", { name: "New capture" }));
  for (const name of [
    "Persona name",
    "Biography",
    "Human contribution",
    "AI disclosure",
  ])
    fireEvent.change(screen.getByLabelText(name), {
      target: { value: "Authored detail" },
    });
  const panel = helper();
  expect(
    within(panel).getByText("What happens after saving?").closest("details")
      ?.open,
  ).toBe(false);
  fireEvent.click(
    within(panel).getByRole("button", { name: "Next: Choose portrait" }),
  );
  expect(document.activeElement).toBe(screen.getByLabelText("Choose photo"));
  expect(write).not.toHaveBeenCalled();
  expect(
    (
      screen.getByRole("button", {
        name: "Register persona",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
});
