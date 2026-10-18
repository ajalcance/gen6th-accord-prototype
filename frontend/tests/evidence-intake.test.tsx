import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import EvidenceIntake from "../app/passport/evidence-intake";
import type { AssetRegistry } from "../lib/persona-assets";
import { ApiError } from "../lib/api-client";
import { evidence, evidenceFixture } from "./evidence-fixtures";

beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:fixture");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function choose() {
  const file = new File(["text"], "creation.txt", { type: "text/plain" });
  Object.defineProperty(file, "arrayBuffer", {
    value: async () => new TextEncoder().encode("text").buffer,
  });
  fireEvent.change(screen.getByLabelText("Evidence file"), {
    target: { files: [file] },
  });
}
it("selects without uploading, manually inspects, then requires separate asset confirmation", async () => {
  const gateway = evidenceFixture(),
    registry: AssetRegistry = {
      workspaceId: evidence.workspace_id,
      enroll: vi.fn(async (command) => ({
        workspace_id: evidence.workspace_id,
        version_id: command.version_id,
        evidence_id: command.evidence_id,
        asset: {
          id: crypto.randomUUID(),
          digest: evidence.sha256,
          label: command.label,
        },
      })),
    };
  render(
    <EvidenceIntake
      gateway={gateway}
      registry={registry}
      versionId={evidence.version_id}
      denied={vi.fn()}
    />,
  );
  choose();
  await screen.findByText(/creation.txt/);
  expect(gateway.upload).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Upload private evidence" }),
  );
  await screen.findByText(/quarantined · expires/);
  expect(
    screen.queryByRole("button", { name: "Download inspected evidence" }),
  ).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Inspect evidence" }));
  await screen.findByRole("button", { name: "Download inspected evidence" });
  expect(registry.enroll).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Asset label"), {
    target: { value: "Fictional scene" },
  });
  fireEvent.change(screen.getByLabelText("Permission or licence basis"), {
    target: { value: "Owner-created fixture" },
  });
  expect(
    (
      screen.getByRole("button", {
        name: "Register production asset",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  fireEvent.click(screen.getByRole("checkbox", { name: /I am authorized/ }));
  fireEvent.click(
    screen.getByRole("button", { name: "Register production asset" }),
  );
  await screen.findByText(/Registered Fictional scene/);
  fireEvent.click(
    screen.getByRole("button", { name: "Download inspected evidence" }),
  );
  const download = await screen.findByRole("link", {
    name: "Download inspected bytes",
  });
  await waitFor(() =>
    expect(download.getAttribute("href")).toBe("blob:fixture"),
  );
  expect(URL.revokeObjectURL).not.toHaveBeenCalled();
  choose();
  await waitFor(() =>
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fixture"),
  );
});
it("keeps the exact upload intent after an uncertain outcome", async () => {
  const gateway = evidenceFixture();
  gateway.upload = vi
    .fn()
    .mockRejectedValueOnce(new ApiError("unavailable", 503))
    .mockResolvedValue(evidence);
  render(
    <EvidenceIntake
      gateway={gateway}
      versionId={evidence.version_id}
      denied={vi.fn()}
    />,
  );
  choose();
  await screen.findByText(/creation.txt/);
  fireEvent.click(
    screen.getByRole("button", { name: "Upload private evidence" }),
  );
  await screen.findByRole("alert");
  fireEvent.click(
    screen.getByRole("button", { name: "Upload private evidence" }),
  );
  await screen.findByText(/quarantined · expires/);
  expect(vi.mocked(gateway.upload).mock.calls[0][0]).toBe(
    vi.mocked(gateway.upload).mock.calls[1][0],
  );
});
it("ignores cancelled late results and denies missing providers", async () => {
  const gateway = evidenceFixture();
  let finish: (value: typeof evidence) => void = () => {};
  gateway.upload = vi.fn(
    () =>
      new Promise<typeof evidence>((resolve) => {
        finish = resolve;
      }),
  );
  const view = render(
    <EvidenceIntake
      gateway={gateway}
      versionId={evidence.version_id}
      denied={vi.fn()}
    />,
  );
  choose();
  await screen.findByText(/creation.txt/);
  fireEvent.click(
    screen.getByRole("button", { name: "Upload private evidence" }),
  );
  await waitFor(() => expect(gateway.upload).toHaveBeenCalled());
  fireEvent.click(screen.getByRole("button", { name: "Stop request" }));
  await act(async () => finish(evidence));
  expect(screen.queryByText(/quarantined · expires/)).toBeNull();
  view.unmount();
  gateway.readiness = vi.fn(async () => ({
    upload_available: false,
    inspection_available: false,
    download_available: false,
    purge_available: false,
  }));
  render(
    <EvidenceIntake
      gateway={gateway}
      versionId={evidence.version_id}
      denied={vi.fn()}
    />,
  );
  await screen.findByText(/Evidence upload unavailable/);
  choose();
  await screen.findByText(/creation.txt/);
  expect(
    (
      screen.getByRole("button", {
        name: "Upload private evidence",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
});
