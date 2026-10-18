import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PublicPassport from "../app/passport/public-passport";
import { apiClient } from "../lib/api-client";
import { publicationFixture } from "./evidence-fixtures";
import { parsePublicPage } from "../lib/persona-publications";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
it("keeps stored passport integrity separate from rejected uploaded verification", async () => {
  const receipt = publicationFixture();
  const page = {
    package: receipt.package,
    verification: {
      integrity: "valid",
      current_use: "eligible",
      evaluated_at: "2026-10-05T00:00:00Z",
    },
  };
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:fixture");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
  const get = vi.spyOn(apiClient, "get").mockResolvedValue(page);
  const post = vi.spyOn(apiClient, "post").mockResolvedValue({
    ...page,
    verification: {
      ...page.verification,
      integrity: "invalid_signature",
      current_use: "unavailable",
    },
  });
  render(
    <PublicPassport
      workspace={receipt.workspace_id}
      publication={receipt.publication_id}
    />,
  );
  await screen.findByText(/Signature: valid/);
  fireEvent.change(screen.getByRole("textbox"), {
    target: { value: JSON.stringify(receipt.package) },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Verify downloaded public package" }),
  );
  await screen.findByText(/Uploaded package: invalid_signature/);
  expect(screen.getByText(/Signature: valid/)).toBeDefined();
  await waitFor(() => expect(post).toHaveBeenCalledTimes(1));
  expect(get).toHaveBeenCalledWith(
    expect.stringContaining("/api/public/passports/"),
    expect.objectContaining({
      credentials: "omit",
      cache: "no-store",
      retries: 0,
    }),
  );
});
it("refuses eligibility attached to an invalid signature", () => {
  const receipt = publicationFixture();
  expect(() =>
    parsePublicPage(
      {
        package: receipt.package,
        verification: {
          integrity: "invalid_signature",
          current_use: "eligible",
          evaluated_at: "2026-10-05T00:00:00Z",
        },
      },
      receipt.publication_id,
    ),
  ).toThrow();
});
