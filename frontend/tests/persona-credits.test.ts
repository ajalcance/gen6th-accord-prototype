import { expect, it, vi } from "vitest";
import {
  creditGateway,
  parseCreditContent,
  parseCreditProfile,
  parseSaveCredits,
} from "../lib/persona-credits";
import { ContractError } from "../lib/persona-validation";
import {
  creditContent,
  creditProfile,
  creditSnapshot,
  creditConfirmation,
} from "./credit-fixtures";
import { version } from "./prepared-write-fixtures";

it("rejects duplicate or oversized aliases, credit count, organization account links and forged trust fields", () => {
  for (const aliases of [
    ["Nova", "nova"],
    ["x".repeat(81)],
    Array.from({ length: 9 }, (_, i) => String(i)),
  ])
    expect(() => parseCreditContent({ ...creditContent, aliases })).toThrow(
      ContractError,
    );
  expect(() =>
    parseCreditContent({
      aliases: [],
      credits: Array(13).fill(creditContent.credits[0]),
    }),
  ).toThrow();
  expect(() =>
    parseCreditContent({
      aliases: [],
      credits: [{ ...creditContent.credits[0], kind: "organization" }],
    }),
  ).toThrow();
  expect(() =>
    parseCreditContent({
      aliases: [],
      credits: [{ ...creditContent.credits[0], state: "confirmed" }],
    }),
  ).toThrow();
});
it("rejects confirmation with a different actor, profile, index or duplicated slot", () => {
  expect(
    parseCreditProfile({
      ...creditProfile,
      confirmations: [creditConfirmation],
    }).confirmations,
  ).toHaveLength(1);
  for (const update of [
    { actor_ref: "creator" },
    { profile_id: version.version_id },
    { credit_index: 1 },
    { workspace_id: version.version_id },
  ])
    expect(() =>
      parseCreditProfile({
        ...creditProfile,
        confirmations: [{ ...creditConfirmation, ...update }],
      }),
    ).toThrow();
  expect(() =>
    parseCreditProfile({
      ...creditProfile,
      confirmations: [creditConfirmation, creditConfirmation],
    }),
  ).toThrow();
  expect(() =>
    parseCreditProfile({
      ...creditProfile,
      snapshot: null,
      confirmations: [creditConfirmation],
    }),
  ).toThrow();
});
it("bounds multibyte metadata before sending it", () => {
  const glyph = String.fromCodePoint(0x1f600);
  expect(() =>
    parseCreditContent({
      aliases: Array.from(
        { length: 8 },
        (_, i) => glyph.repeat(78) + String(i),
      ),
      credits: Array.from({ length: 12 }, (_, i) => ({
        ...creditContent.credits[0],
        name: glyph.repeat(78) + String(i),
        actor_ref: glyph.repeat(64),
      })),
    }),
  ).toThrow(ContractError);
});
it("binds every read to workspace/version and distinguishes missing from invalid data", async () => {
  const transport = vi
    .fn()
    .mockResolvedValue({ ...creditProfile, snapshot: null });
  const gateway = creditGateway(version.workspace_id, transport),
    signal = new AbortController().signal;
  expect((await gateway.read(version.version_id, signal)).snapshot).toBeNull();
  transport.mockResolvedValue({
    ...creditProfile,
    version_id: creditSnapshot.id,
  });
  await expect(gateway.read(version.version_id, signal)).rejects.toThrow();
  transport.mockResolvedValue({
    ...creditProfile,
    workspace_id: creditSnapshot.id,
  });
  await expect(gateway.read(version.version_id, signal)).rejects.toThrow();
});
it("sends creator content only and rejects changed save receipts", async () => {
  const command = {
    request_id: creditSnapshot.request_id,
    version_id: version.version_id,
    expected_previous_id: null,
    content: creditContent,
  };
  const transport = vi.fn().mockResolvedValue(creditSnapshot),
    signal = new AbortController().signal;
  const gateway = creditGateway(version.workspace_id, transport);
  await gateway.save(command, signal);
  expect(transport.mock.calls[0][1]).toEqual(command);
  expect(() =>
    parseSaveCredits({ ...command, declared_by: "browser" }),
  ).toThrow();
  transport.mockResolvedValue({
    ...creditSnapshot,
    content: { aliases: [], credits: [] },
  });
  await expect(gateway.save(command, signal)).rejects.toThrow();
});
it("binds confirmation to the exact slot and ignores completion after cancellation", async () => {
  const command = {
    request_id: creditConfirmation.request_id,
    version_id: version.version_id,
    profile_id: creditSnapshot.id,
    credit_index: 0,
  };
  const controller = new AbortController(),
    transport = vi
      .fn()
      .mockResolvedValue({ ...creditConfirmation, credit_index: 1 });
  const gateway = creditGateway(version.workspace_id, transport);
  await expect(gateway.confirm(command, controller.signal)).rejects.toThrow();
  transport.mockImplementation(async () => {
    controller.abort();
    return creditConfirmation;
  });
  await expect(
    gateway.confirm(command, controller.signal),
  ).rejects.toMatchObject({ name: "AbortError" });
});
