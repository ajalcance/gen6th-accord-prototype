import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import PassportBooklet from "../app/passport/passport-booklet";
import SavedPassports from "../app/passport/saved-passports";
import { GovernanceAccessLoss } from "../app/passport/saved-governance-read";
import { ApiError } from "../lib/api-client";
import { personaGateway } from "../lib/persona-gateway";
import { bookletSource } from "./booklet-fixtures";
import { offer, packageFixture, version } from "./passport-fixtures";

const replacements: {
  object: object;
  key: string;
  descriptor: PropertyDescriptor | undefined;
}[] = [];
function replace(object: object, key: string, value: unknown) {
  replacements.push({
    object,
    key,
    descriptor: Object.getOwnPropertyDescriptor(object, key),
  });
  Object.defineProperty(object, key, {
    configurable: true,
    writable: true,
    value,
  });
}
beforeEach(() => {
  replace(
    URL,
    "createObjectURL",
    vi.fn(() => "blob:fictional-reference"),
  );
  replace(URL, "revokeObjectURL", vi.fn());
  replace(
    HTMLDialogElement.prototype,
    "showModal",
    function (this: HTMLDialogElement) {
      this.setAttribute("open", "");
    },
  );
  replace(
    HTMLDialogElement.prototype,
    "close",
    function (this: HTMLDialogElement) {
      this.removeAttribute("open");
    },
  );
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  for (const entry of replacements.splice(0)) {
    if (entry.descriptor)
      Object.defineProperty(entry.object, entry.key, entry.descriptor);
    else Reflect.deleteProperty(entry.object, entry.key);
  }
});
function open() {
  fireEvent.click(screen.getByRole("button", { name: "View passport" }));
}
it("waits for authorized scope discovery instead of claiming an unknown offer is absent", () => {
  const source = bookletSource();
  vi.spyOn(source.gateway.governance, "campaigns").mockImplementation(
    () => new Promise(() => {}),
  );
  render(<SavedPassports source={source} version={version} />);
  const button = screen.getByRole("button", { name: "View passport" });
  expect((button as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(button);
  expect(screen.queryByRole("dialog")).toBeNull();
});
it("opens no-offer/no-portrait preview without a seal or QR", async () => {
  const source = bookletSource();
  source.captures = undefined;
  source.gateway = personaGateway(version.workspace_id, async () => ({
    items: [],
    next_after_id: null,
  }));
  render(<SavedPassports source={source} version={version} />);
  await screen.findByText(/No production offers for this version/);
  open();
  await screen.findByText(
    "Saved records loaded. Refresh permission before use.",
  );
  expect(screen.getByLabelText("Registered passport preview")).toBeDefined();
  expect(screen.getByText("Not assigned")).toBeDefined();
  expect(screen.getByText("Approved portrait unavailable")).toBeDefined();
  expect(
    screen.getByText("Accord record, not a government document"),
  ).toBeDefined();
  expect(
    screen.queryByRole("img", { name: "QR code for approved public passport" }),
  ).toBeNull();
  expect(screen.queryByText(/Digitally signed/)).toBeNull();
  expect(source.passports!.export).not.toHaveBeenCalled();
});
it("shows the issued seal/QR only with a server-verified package and approved sharing", async () => {
  const source = bookletSource();
  render(
    <PassportBooklet
      source={source}
      version={version}
      offer={offer}
      packet={packageFixture()}
    />,
  );
  open();
  await screen.findByLabelText("Issued persona passport");
  expect(
    screen.getByRole("img", { name: "QR code for approved public passport" }),
  ).toBeDefined();
  expect(screen.getByText(/Digitally signed/)).toBeDefined();
  expect(screen.getByText("2026-10-02T04:05:00.000Z")).toBeDefined();
  expect(screen.getByText(/Creator statements:/).textContent).toContain(
    version.content.ai_disclosure,
  );
  expect(screen.getByText(/Recorded offer:/).textContent).toContain(
    offer.scope.recipient_ref,
  );
  expect(source.publications!.approve).not.toHaveBeenCalled();
});
it("clears the seal and QR while refreshing and after public withdrawal", async () => {
  const source = bookletSource();
  render(
    <PassportBooklet
      source={source}
      version={version}
      offer={offer}
      packet={packageFixture()}
    />,
  );
  open();
  await screen.findByLabelText("Issued persona passport");
  vi.mocked(source.publications!.history).mockResolvedValue({
    items: [],
    next: null,
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Refresh passport records" }),
  );
  expect(
    screen.queryByRole("img", { name: "QR code for approved public passport" }),
  ).toBeNull();
  await screen.findByText(
    "Saved records loaded. Refresh permission before use.",
  );
  expect(screen.queryByLabelText("Issued persona passport")).toBeNull();
});
it("clears private booklet content on denied access", async () => {
  const source = bookletSource(),
    denied = vi.fn();
  vi.mocked(source.captures!.query).mockRejectedValue(
    new ApiError("Denied", 403),
  );
  render(
    <GovernanceAccessLoss.Provider value={denied}>
      <PassportBooklet
        source={source}
        version={version}
        offer={offer}
        packet={null}
      />
    </GovernanceAccessLoss.Provider>,
  );
  open();
  await waitFor(() => expect(denied).toHaveBeenCalled());
  expect(screen.queryByLabelText("Registered passport preview")).toBeNull();
});
it("preserves an explicit package across private/public controls and clears it for another session", async () => {
  const source = bookletSource();
  const mounted = render(<SavedPassports source={source} version={version} />);
  await screen.findByRole("button", { name: "Prepare signed passport" });
  fireEvent.click(
    screen.getByRole("checkbox", { name: /Share this exact version/ }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Prepare signed passport" }),
  );
  await screen.findByRole("link", { name: "Download passport JSON" });
  fireEvent.click(screen.getByRole("button", { name: "Public sharing" }));
  open();
  await screen.findByLabelText("Issued persona passport");
  fireEvent.click(screen.getByRole("button", { name: "Close passport" }));
  mounted.rerender(
    <SavedPassports
      source={{ ...source, sessionKey: "another-fictional-session" }}
      version={version}
    />,
  );
  await screen.findByRole("button", { name: "Prepare signed passport" });
  open();
  await screen.findByText(
    "Saved records loaded. Refresh permission before use.",
  );
  expect(screen.queryByLabelText("Issued persona passport")).toBeNull();
  expect(source.passports!.export).toHaveBeenCalledTimes(1);
});
it("closes on cancel, restores the opening control and revokes the portrait object URL", async () => {
  const source = bookletSource();
  render(
    <PassportBooklet
      source={source}
      version={version}
      offer={offer}
      packet={null}
    />,
  );
  const button = screen.getByRole("button", { name: "View passport" });
  button.focus();
  open();
  await screen.findByAltText(`Approved reference for ${version.content.name}`);
  fireEvent(screen.getByRole("dialog"), new Event("cancel", { bubbles: true }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(document.activeElement).toBe(button);
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fictional-reference");
});
