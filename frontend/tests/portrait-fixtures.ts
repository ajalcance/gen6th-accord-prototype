/** Explicit synthetic inspection receipts; no real scanner/provider acceptance. */
import { fireEvent, screen } from "@testing-library/react";
import type { PhotoGateway } from "../lib/persona-photos";

export function portraitGateway(workspaceId: string): PhotoGateway {
  return {
    workspaceId,
    upload: async (command) => ({
      id: "00000000-0000-4000-8000-000000000090",
      workspace_id: workspaceId,
      request_id: command.request_id,
      sha256: command.sha256,
      width: 32,
      height: 16,
    }),
    thumbnail: async () => null,
  };
}

export async function scanPortrait() {
  const file = new File(["synthetic"], "portrait.png", { type: "image/png" });
  Object.defineProperty(file, "arrayBuffer", {
    value: async () => new TextEncoder().encode("synthetic").buffer,
  });
  fireEvent.change(screen.getByLabelText("Choose photo"), {
    target: { files: [file] },
  });
  const scan = screen.getByRole("button", {
    name: "Scan",
  }) as HTMLButtonElement;
  if (!scan.disabled) {
    fireEvent.click(scan);
    await screen.findByText(/Scan complete\. Save/);
  }
}
