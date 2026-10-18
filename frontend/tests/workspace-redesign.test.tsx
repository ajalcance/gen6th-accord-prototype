import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PassportStudio from "../app/passport/studio";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import { preparedSource, version } from "./prepared-write-fixtures";
import wire from "./fixtures/persona-wire.json";
import CopyReference from "../app/passport/copy-reference";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
const click = (name: string) =>
  fireEvent.click(screen.getByRole("button", { name }));
const journey = () =>
  within(screen.getByRole("navigation", { name: "Persona journey" }));

it("keeps image modes beside name search and never starts processing on disclosure", async () => {
  const source = preparedSource(),
    search = vi.fn();
  source.portraitSearch = { workspaceId: source.workspaceId, search };
  render(<PassportStudio savedSource={source} />);
  await screen.findByRole("button", { name: /Open record/ });
  const tools = screen.getByLabelText("Record tools");
  fireEvent.click(
    within(tools).getByRole("button", { name: "Search by image" }),
  );
  expect(screen.getByRole("region", { name: "Search by image" })).toBeDefined();
  expect(
    screen.queryByRole("list", { name: "grid of workspace personas" }),
  ).toBeNull();
  click("Similar face");
  expect(screen.queryByLabelText("Choose search image")).toBeNull();
  click("Identical file");
  click("Return to all records");
  expect(document.activeElement).toBe(
    within(tools).getByRole("button", { name: "Search by image" }),
  );
  expect(search).not.toHaveBeenCalled();
});

it("retains a bounded catalogue page, submitted search and display when returning from a record", async () => {
  const second = {
    ...wire.version,
    persona_id: "ffffffff-ffff-4fff-8fff-ffffffffffff",
  };
  const first = Array.from({ length: 20 }, (_, i) => ({
    ...wire.version,
    persona_id: `00000000-0000-4000-8000-${String(i + 1).padStart(12, "0")}`,
  }));
  const read = vi.fn<PersonaTransport>(
    async (operation, _workspace, command) =>
      operation === "load"
        ? second
        : {
            workspace_id: version.workspace_id,
            items: (command as { after_persona_id: string | null })
              .after_persona_id
              ? [second]
              : first,
            next_after_persona_id: (
              command as { after_persona_id: string | null }
            ).after_persona_id
              ? null
              : first[19].persona_id,
          },
  );
  const source = preparedSource();
  source.gateway = personaGateway(source.workspaceId, read);
  render(<PassportStudio savedSource={source} />);
  await screen.findAllByRole("button", { name: /Open record/ });
  fireEvent.change(screen.getByRole("searchbox"), {
    target: { value: "Fictional" },
  });
  click("Search records");
  await screen.findAllByRole("button", { name: /Open record/ });
  click("List view");
  fireEvent.click(
    within(
      screen.getByRole("navigation", { name: "Record pages top" }),
    ).getByRole("button", { name: "Next page" }),
  );
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  await screen.findByRole("heading", { name: version.content.name });
  click("Back to saved records");
  await screen.findByRole("list", { name: "list of workspace personas" });
  expect((screen.getByRole("searchbox") as HTMLInputElement).value).toBe(
    "Fictional",
  );
  expect(read.mock.calls.at(-1)?.[2]).toEqual({
    search: "Fictional",
    limit: 20,
    after_persona_id: first[19].persona_id,
  });
});

it("pins the loaded version across workflows, permits explicit current-version reload and clears selection on a new session", async () => {
  const newer = {
    ...wire.version,
    revision: 2,
    version_id: wire.save.request_id,
  };
  let head = wire.version;
  const read = vi.fn<PersonaTransport>(
    async (operation, _workspace, command) => {
      if (operation === "gallery") return wire.gallery;
      if (operation === "load")
        return (command as { revision: number | null }).revision === 1
          ? wire.version
          : head;
      if (operation === "versionHistory")
        return { items: [newer, wire.version], next_before_revision: null };
      return { items: [], next_after_id: null };
    },
  );
  const source = preparedSource();
  source.gateway = personaGateway(source.workspaceId, read);
  const mounted = render(<PassportStudio savedSource={source} />);
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  await screen.findByRole("heading", { name: version.content.name });
  head = newer;
  fireEvent.click(journey().getByRole("button", { name: "Production & use" }));
  await screen.findByRole("button", { name: "Version 1 · Change version" });
  expect(read.mock.calls.filter(([op]) => op === "load").at(-1)?.[2]).toEqual({
    persona_id: version.persona_id,
    revision: 1,
  });
  click("Version 1 · Change version");
  click("Load current version");
  await screen.findByRole("button", { name: "Version 2 · Change version" });
  click("Version 2 · Change version");
  click("Load current version");
  await screen.findByRole("button", { name: "Version 2 · Change version" });
  mounted.rerender(
    <PassportStudio savedSource={{ ...source, sessionKey: "new-session" }} />,
  );
  await screen.findByRole("heading", { name: "Choose a performer" });
  expect(screen.queryByRole("button", { name: /Change version/ })).toBeNull();
});

it("offers a performer picker on workflow entry and exposes local settings without activating services", async () => {
  const source = preparedSource();
  render(<PassportStudio savedSource={source} />);
  fireEvent.click(journey().getByRole("button", { name: "Analysis & review" }));
  expect(
    screen.getByRole("heading", { name: "Choose a performer" }),
  ).toBeDefined();
  fireEvent.click(
    await screen.findByRole("button", {
      name: new RegExp(version.content.name),
    }),
  );
  await screen.findByRole("button", { name: /Change version/ });
  click("Settings");
  click("Recognition evidence");
  expect(screen.getByText(/Recognition accuracy is unmeasured/)).toBeDefined();
  click("Preferences");
  click("List view");
  fireEvent.click(journey().getByRole("button", { name: "Records" }));
  await screen.findByRole("list", { name: "list of workspace personas" });
});

it("fails closed before direct write controls mount with a mismatched gateway", async () => {
  const source = preparedSource(),
    write = vi.fn();
  source.writeGateway = personaGateway(wire.campaign.id, write);
  render(<PassportStudio savedSource={source} />);
  fireEvent.click(await screen.findByRole("button", { name: /Open record/ }));
  await screen.findByText("The write connection could not be validated.");
  expect(screen.queryByRole("button", { name: "Edit persona" })).toBeNull();
  fireEvent.click(journey().getByRole("button", { name: "Production & use" }));
  await screen.findByText("The write connection could not be validated.");
  expect(screen.queryByRole("button", { name: "Create offer" })).toBeNull();
  expect(write).not.toHaveBeenCalled();
});

it("copies only the selected technical reference and explains clipboard denial", async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal("navigator", { clipboard: { writeText } });
  render(<CopyReference value="synthetic-reference" label="digest" />);
  click("Copy digest");
  await waitFor(() =>
    expect(writeText).toHaveBeenCalledWith("synthetic-reference"),
  );
  writeText.mockRejectedValue(new Error("Unavailable"));
  click("Copy digest");
  await act(async () => {});
  expect(screen.getByRole("status").textContent).toMatch(
    /select|manually|unavailable/i,
  );
});
