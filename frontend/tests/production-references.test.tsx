import { useState } from "react";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import ProductionReferences from "../app/passport/production-references";
import { GovernanceAccessLoss } from "../app/passport/saved-governance-read";
import type { SavedPersonaSource } from "../app/passport/saved-source";
import { ApiError } from "../lib/api-client";
import { personaGateway, type PersonaTransport } from "../lib/persona-gateway";
import { preparedSource, version } from "./prepared-write-fixtures";

afterEach(cleanup);
function Editor({ source }: { source: SavedPersonaSource }) {
  const [fields, setFields] = useState<Record<string, string>>({
    references: "",
    confirm: "yes",
  });
  return (
    <>
      <ProductionReferences
        source={source}
        versionId={version.version_id}
        draft={{
          fields,
          store: null,
          change: (field, value) =>
            setFields({ ...fields, [field]: value, confirm: "" }),
          changeFields: (values) =>
            setFields({ ...fields, ...values, confirm: "" }),
        }}
      />
      <output aria-label="Submitted references">{fields.references}</output>
      <output aria-label="Confirmation">{fields.confirm}</output>
    </>
  );
}
const rows = Array.from({ length: 10 }, (_, i) => ({
  id: `00000000-0000-4000-8000-${String(i + 100).padStart(12, "0")}`,
  workspace_id: version.workspace_id,
  version_id: version.version_id,
  media_type: "text/plain",
  byte_length: 12,
  sha256: "a".repeat(64),
  recorded_at: i === 9 ? "2020-01-01T00:00:00Z" : "2099-01-01T00:00:00Z",
  expires_at: i === 9 ? "2020-01-08T00:00:00Z" : "2099-01-08T00:00:00Z",
  state: "clean",
}));
it("loads only scoped metadata on demand, bounds selection and clears confirmation when claims change", async () => {
  const source = preparedSource(),
    read = vi.fn<PersonaTransport>(async () => ({
      items: rows,
      next_after_id: null,
    }));
  source.gateway = personaGateway(source.workspaceId, read);
  render(<Editor source={source} />);
  expect(read).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Choose supporting evidence" }),
  );
  await screen.findByRole("combobox", { name: `Use evidence ${rows[0].id}` });
  expect(read.mock.calls[0][2]).toMatchObject({
    version_id: version.version_id,
    limit: 20,
  });
  expect(
    (
      screen.getByRole("combobox", {
        name: `Use evidence ${rows[9].id}`,
      }) as HTMLSelectElement
    ).disabled,
  ).toBe(true);
  for (const row of rows.slice(0, 8))
    fireEvent.change(
      screen.getByRole("combobox", { name: `Use evidence ${row.id}` }),
      { target: { value: "consent" } },
    );
  expect(
    (
      screen.getByRole("combobox", {
        name: `Use evidence ${rows[8].id}`,
      }) as HTMLSelectElement
    ).disabled,
  ).toBe(true);
  expect(screen.getByLabelText("Confirmation").textContent).toBe("");
  fireEvent.change(
    screen.getByRole("combobox", { name: `Use evidence ${rows[0].id}` }),
    { target: { value: "claim" } },
  );
  expect(screen.getByLabelText("Submitted references").textContent).toContain(
    `claim:${rows[0].id}`,
  );
  fireEvent.click(
    screen.getByRole("button", { name: `Remove reference ${rows[0].id}` }),
  );
  expect(
    (
      screen.getByRole("combobox", {
        name: `Use evidence ${rows[8].id}`,
      }) as HTMLSelectElement
    ).disabled,
  ).toBe(false);
  expect(read).toHaveBeenCalledTimes(1);
});
it("propagates metadata access loss and discards late results when the picker closes", async () => {
  const source = preparedSource(),
    denied = vi.fn();
  let resolve!: (value: unknown) => void;
  const read = vi
    .fn<PersonaTransport>()
    .mockImplementationOnce(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    )
    .mockRejectedValue(new ApiError("Denied", 403));
  source.gateway = personaGateway(source.workspaceId, read);
  render(
    <GovernanceAccessLoss.Provider value={denied}>
      <Editor source={source} />
    </GovernanceAccessLoss.Provider>,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Choose supporting evidence" }),
  );
  await waitFor(() => expect(read).toHaveBeenCalledTimes(1));
  fireEvent.click(
    screen.getByRole("button", { name: "Close evidence picker" }),
  );
  await act(async () => resolve({ items: rows, next_after_id: null }));
  expect(screen.queryByRole("combobox")).toBeNull();
  fireEvent.click(
    screen.getByRole("button", { name: "Choose supporting evidence" }),
  );
  await waitFor(() => expect(denied).toHaveBeenCalled());
  expect(screen.queryByRole("combobox")).toBeNull();
});
