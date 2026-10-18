import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import PassportActions from "../app/passport/passport-actions";
import { GovernanceAccessLoss } from "../app/passport/saved-governance-read";
import { ApiError } from "../lib/api-client";
import {
  gatewayFixture,
  offer,
  packageFixture,
  status,
  version,
} from "./passport-fixtures";
import type { PassportGateway } from "../lib/persona-passports";
import type { PassportVerification } from "../lib/persona-passport-contracts";

beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:synthetic-passport");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function mount(gateway: PassportGateway, eligible = true, denied = vi.fn()) {
  return render(
    <GovernanceAccessLoss.Provider value={denied}>
      <PassportActions
        gateway={gateway}
        version={version}
        offer={offer}
        eligible={eligible}
      />
    </GovernanceAccessLoss.Provider>,
  );
}
async function enterPackage() {
  await screen.findByLabelText("Passport JSON");
  fireEvent.change(screen.getByLabelText("Passport JSON"), {
    target: { value: JSON.stringify(packageFixture()) },
  });
}
it("requires sharing confirmation, exports only on click and revokes the download URL", async () => {
  const gateway = gatewayFixture(),
    mounted = mount(gateway);
  const submit = (await screen.findByRole("button", {
    name: "Prepare signed passport",
  })) as HTMLButtonElement;
  expect(submit.disabled).toBe(true);
  expect(gateway.export).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("checkbox", { name: /Share this exact version/ }),
  );
  fireEvent.click(submit);
  expect(
    (
      await screen.findByRole("link", { name: "Download passport JSON" })
    ).getAttribute("download"),
  ).toBe("accord-persona-passport.json");
  expect(gateway.export).toHaveBeenCalledWith(
    version,
    offer,
    expect.any(AbortSignal),
  );
  mounted.unmount();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:synthetic-passport");
});
it("shows an explicit altered-package result and clears it when input changes", async () => {
  const gateway = gatewayFixture();
  vi.mocked(gateway.verify).mockResolvedValue({
    workspace_id: version.workspace_id,
    campaign_id: offer.id,
    integrity: "invalid_signature",
    current_status: null,
  });
  mount(gateway);
  await enterPackage();
  fireEvent.click(
    screen.getByRole("button", { name: "Verify passport package" }),
  );
  await screen.findByText("Altered package or invalid signature");
  expect(screen.queryByText(/Recorded production scope eligible/)).toBeNull();
  fireEvent.change(screen.getByLabelText("Passport JSON"), {
    target: { value: "{}" },
  });
  expect(screen.queryByText("Altered package or invalid signature")).toBeNull();
});
it("keeps signature validity separate from revoked permission", async () => {
  const gateway = gatewayFixture();
  vi.mocked(gateway.verify).mockResolvedValue({
    workspace_id: version.workspace_id,
    campaign_id: offer.id,
    integrity: "valid",
    current_status: {
      ...status,
      eligible_for_use: false,
      blocking_reasons: ["revoked"],
    },
  });
  mount(gateway, false);
  await enterPackage();
  expect(
    (
      screen.getByRole("button", {
        name: "Prepare signed passport",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  fireEvent.click(
    screen.getByRole("button", { name: "Verify passport package" }),
  );
  await screen.findByText("Signature valid · package matches saved production");
  expect(screen.getByText("Current production use blocked")).toBeDefined();
  expect(screen.getByText("revoked")).toBeDefined();
});
it("keeps unavailable adapters disabled and never fabricates an unsigned export", async () => {
  const gateway = gatewayFixture();
  vi.mocked(gateway.readiness).mockResolvedValue({
    workspace_id: version.workspace_id,
    export_available: false,
    verification_available: false,
  });
  mount(gateway);
  await screen.findByText(
    "Passport signing is not configured on this connection.",
  );
  expect(
    screen.getByText(
      "Trusted verification keys are not configured on this connection.",
    ),
  ).toBeDefined();
  expect(
    (
      screen.getByRole("button", {
        name: "Prepare signed passport",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  expect(
    (
      screen.getByRole("button", {
        name: "Verify passport package",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  expect(gateway.export).not.toHaveBeenCalled();
});
it("ignores late verification after unmount and propagates permission loss", async () => {
  const gateway = gatewayFixture();
  let finish!: (result: PassportVerification) => void;
  vi.mocked(gateway.verify).mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const mounted = mount(gateway);
  await enterPackage();
  fireEvent.click(
    screen.getByRole("button", { name: "Verify passport package" }),
  );
  mounted.unmount();
  await act(async () =>
    finish({
      workspace_id: version.workspace_id,
      campaign_id: offer.id,
      integrity: "valid",
      current_status: status,
    }),
  );
  expect(screen.queryByText(/Signature valid/)).toBeNull();
  vi.mocked(gateway.verify).mockRejectedValue(new ApiError("denied", 403));
  const denied = vi.fn();
  mount(gateway, true, denied);
  await enterPackage();
  fireEvent.click(
    screen.getByRole("button", { name: "Verify passport package" }),
  );
  await screen.findByText(/access is no longer available/);
  expect(denied).toHaveBeenCalled();
});
it("rejects oversized files before reading and never verifies malformed input", async () => {
  const gateway = gatewayFixture();
  mount(gateway);
  await screen.findByLabelText("Choose passport JSON");
  const file = new File(["x".repeat(65537)], "large.json", {
    type: "application/json",
  });
  fireEvent.change(screen.getByLabelText("Choose passport JSON"), {
    target: { files: [file] },
  });
  await screen.findByText(/within 64 KiB/);
  fireEvent.change(screen.getByLabelText("Passport JSON"), {
    target: { value: "invalid" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Verify passport package" }),
  );
  await screen.findByText(/valid bounded JSON/);
  expect(gateway.verify).not.toHaveBeenCalled();
});

it("previews a file only and ignores late file reads after a newer paste", async () => {
  const gateway = gatewayFixture();
  mount(gateway);
  await screen.findByLabelText("Choose passport JSON");
  const file = new File(["{}"], "passport.json", { type: "application/json" });
  let finish!: (text: string) => void;
  Object.defineProperty(file, "text", {
    value: () =>
      new Promise<string>((resolve) => {
        finish = resolve;
      }),
  });
  fireEvent.change(screen.getByLabelText("Choose passport JSON"), {
    target: { files: [file] },
  });
  fireEvent.change(screen.getByLabelText("Passport JSON"), {
    target: { value: "newer paste" },
  });
  await act(async () => finish(JSON.stringify(packageFixture())));
  expect(
    (screen.getByLabelText("Passport JSON") as HTMLTextAreaElement).value,
  ).toBe("newer paste");
  expect(gateway.verify).not.toHaveBeenCalled();
});
