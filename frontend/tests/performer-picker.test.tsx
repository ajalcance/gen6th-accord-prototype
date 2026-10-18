import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PassportStudio from "../app/passport/studio";
import PersonaPicker from "../app/passport/persona-picker";
import type { JourneyPage } from "../app/passport/workspace-pages";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import { preparedSource, version } from "./prepared-write-fixtures";
import wire from "./fixtures/persona-wire.json";

afterEach(cleanup);
const cases: [JourneyPage, string, RegExp][] = [
  [
    "Analysis & review",
    "Open analysis",
    /Compare appearances with approved references/,
  ],
  [
    "Production & use",
    "Manage production use",
    /Manage production offers, current permissions/,
  ],
  [
    "Passports",
    "Open passports",
    /Issue private passports, manage public sharing/,
  ],
];
function navigate(page: JourneyPage) {
  fireEvent.click(
    within(
      screen.getByRole("navigation", { name: "Persona journey" }),
    ).getByRole("button", { name: page }),
  );
}

it.each(cases)(
  "explains %s and opens its distinct workspace after deliberate selection",
  async (page, action, purpose) => {
    render(<PassportStudio savedSource={preparedSource()} />);
    navigate(page);
    expect(screen.getByText(purpose)).toBeDefined();
    const picker = screen.getByRole("region", { name: "Choose a performer" });
    const input = within(picker).getByRole("searchbox", {
      name: "Performer name",
    });
    expect(input.getAttribute("placeholder")).toBe("Search by performer name…");
    const choose = await within(picker).findByRole("button", {
      name: `${action} for ${version.content.name}, version 1`,
    });
    expect(
      screen.queryByRole("button", { name: "Change performer" }),
    ).toBeNull();
    fireEvent.click(choose);
    await screen.findByRole("button", { name: "Change performer" });
    expect(
      screen.queryByRole("region", { name: "Choose a performer" }),
    ).toBeNull();
    if (page === "Analysis & review")
      expect(
        screen.getByRole("button", { name: "Independent review" }),
      ).toBeDefined();
    if (page === "Production & use")
      expect(
        screen.getByRole("button", { name: "Current permission" }),
      ).toBeDefined();
    if (page === "Passports")
      expect(
        screen.getByRole("button", { name: "Private issuance" }),
      ).toBeDefined();
  },
);

it("retains the chosen performer and loaded version across all three destinations", async () => {
  render(<PassportStudio savedSource={preparedSource()} />);
  navigate("Analysis & review");
  fireEvent.click(
    await screen.findByRole("button", {
      name: `Open analysis for ${version.content.name}, version 1`,
    }),
  );
  await screen.findByRole("button", { name: "Version 1 · Change version" });
  for (const page of [
    "Production & use",
    "Passports",
    "Analysis & review",
  ] as const) {
    navigate(page);
    await screen.findByRole("button", { name: "Version 1 · Change version" });
    expect(
      screen.queryByRole("region", { name: "Choose a performer" }),
    ).toBeNull();
  }
  fireEvent.click(screen.getByRole("button", { name: "Change performer" }));
  await screen.findByRole("region", { name: "Choose a performer" });
});

it("submits a bounded name search and selects only by the returned performer id", async () => {
  const read = vi.fn<PersonaTransport>(async () => wire.gallery);
  const source = preparedSource();
  source.gateway = personaGateway(source.workspaceId, read);
  const select = vi.fn();
  render(
    <PersonaPicker
      source={source}
      journey="Production & use"
      select={select}
    />,
  );
  await screen.findByRole("button", {
    name: `Manage production use for ${version.content.name}, version 1`,
  });
  fireEvent.change(screen.getByRole("searchbox", { name: "Performer name" }), {
    target: { value: "  Fictional  " },
  });
  fireEvent.submit(
    screen.getByRole("search", { name: "Find a saved performer" }),
  );
  await waitFor(() =>
    expect(read.mock.calls.at(-1)?.[2]).toEqual({
      search: "Fictional",
      limit: 20,
      after_persona_id: null,
    }),
  );
  expect(select).not.toHaveBeenCalled();
  fireEvent.click(
    await screen.findByRole("button", {
      name: `Manage production use for ${version.content.name}, version 1`,
    }),
  );
  expect(select).toHaveBeenCalledExactlyOnceWith(version.persona_id);
});
