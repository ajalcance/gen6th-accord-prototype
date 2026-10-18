import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import PassportPublication from "../app/passport/passport-publication";
import { publicationGatewayFixture } from "./evidence-fixtures";
import { offer, version } from "./passport-fixtures";
import { ApiError } from "../lib/api-client";

beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:fixture");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
it("previews a minimal projection and requires explicit disclosure approval", async () => {
  const gateway = publicationGatewayFixture();
  render(
    <PassportPublication
      gateway={gateway}
      version={version}
      offer={offer}
      eligible
    />,
  );
  expect(
    (
      screen.getByRole("button", {
        name: "Prepare approved public passport",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  expect(gateway.approve).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I approve these fields/ }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Prepare approved public passport" }),
  );
  await screen.findByRole("link", { name: "Open approved public passport" });
  expect(vi.mocked(gateway.approve).mock.calls[0][0].fields).toEqual([
    "name",
    "ai_disclosure",
  ]);
  expect(
    screen.getByRole("img", { name: "QR code for approved public passport" }),
  ).toBeDefined();
  fireEvent.click(
    screen.getByRole("button", { name: "Withdraw public access" }),
  );
  await screen.findByText("Public access withdrawn");
  expect(
    screen.queryByRole("link", { name: "Open approved public passport" }),
  ).toBeNull();
});
it("retries the exact approved projection and locks fields during uncertain outcome", async () => {
  const gateway = publicationGatewayFixture(),
    approval = gateway.approve;
  gateway.approve = vi
    .fn()
    .mockRejectedValueOnce(new ApiError("unavailable", 503))
    .mockImplementation(approval);
  render(
    <PassportPublication
      gateway={gateway}
      version={version}
      offer={offer}
      eligible
    />,
  );
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I approve these fields/ }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Prepare approved public passport" }),
  );
  await screen.findByRole("button", {
    name: "Retry approved passport preparation",
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Retry approved passport preparation" }),
  );
  await screen.findByRole("link", { name: "Open approved public passport" });
  expect(vi.mocked(gateway.approve).mock.calls[0][0]).toBe(
    vi.mocked(gateway.approve).mock.calls[1][0],
  );
});
