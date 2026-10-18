import { expect, it, vi } from "vitest";
import { readBooklet } from "../app/passport/booklet-read";
import { bookletSource } from "./booklet-fixtures";
import { offer, packageFixture, version } from "./passport-fixtures";
import { profile } from "./capture-fixtures";

const signal = () => new AbortController().signal;
it("loads only existing read gateways and never exports or approves", async () => {
  const source = bookletSource();
  const result = await readBooklet(
    { source, version, offer, packet: packageFixture() },
    signal(),
  );
  expect(result.signature?.references).toBe(1);
  expect(result.publication).not.toBeNull();
  expect(result.portrait).toBeInstanceOf(Blob);
  expect(source.passports!.verify).toHaveBeenCalledWith(
    offer.id,
    packageFixture(),
    expect.any(AbortSignal),
  );
  expect(source.passports!.export).not.toHaveBeenCalled();
  expect(source.publications!.approve).not.toHaveBeenCalled();
  expect(source.publications!.unpublish).not.toHaveBeenCalled();
});
it("keeps no-offer records usable without signing, verification or publication calls", async () => {
  const source = bookletSource();
  const result = await readBooklet(
    { source, version, offer: null, packet: null },
    signal(),
  );
  expect(result.status).toBeNull();
  expect(result.signature).toBeNull();
  expect(source.passports!.verify).not.toHaveBeenCalled();
  expect(source.publications!.history).not.toHaveBeenCalled();
});
it("does not query owner-only history for a reviewer opening an unsigned preview", async () => {
  const source = bookletSource();
  vi.mocked(source.publications!.history).mockRejectedValue(
    new Error("Owner-only history must not run"),
  );
  const result = await readBooklet(
    { source, version, offer, packet: null },
    signal(),
  );
  expect(result.status).not.toBeNull();
  expect(source.publications!.history).not.toHaveBeenCalled();
});
it("finds an active approval on a later history page", async () => {
  const source = bookletSource();
  const history = await source.publications!.history(offer.id, null, signal());
  vi.mocked(source.publications!.history)
    .mockResolvedValueOnce({
      items: history.items.map((item) => ({ ...item, withdrawn: true })),
      next: history.items[0].receipt.publication_id,
    })
    .mockResolvedValueOnce(history);
  const result = await readBooklet(
    { source, version, offer, packet: packageFixture() },
    signal(),
  );
  expect(result.publication?.publication_id).toBe(
    history.items[0].receipt.publication_id,
  );
  expect(source.publications!.history).toHaveBeenLastCalledWith(
    offer.id,
    history.items[0].receipt.publication_id,
    expect.any(AbortSignal),
  );
});
it("does not equate inspected portrait with approved reference", async () => {
  const source = bookletSource();
  vi.mocked(source.captures!.query).mockResolvedValue({
    ...profile,
    references: [],
  });
  const result = await readBooklet(
    { source, version, offer, packet: null },
    signal(),
  );
  expect(result.portrait).toBeNull();
  expect(source.captures!.thumbnail).not.toHaveBeenCalled();
});
it("drops the signature after invalid server verification and drops withdrawn sharing", async () => {
  const source = bookletSource();
  vi.mocked(source.passports!.verify).mockResolvedValue({
    workspace_id: version.workspace_id,
    campaign_id: offer.id,
    integrity: "invalid_signature",
    current_status: null,
  });
  const history = await source.publications!.history(offer.id, null, signal());
  vi.mocked(source.publications!.history).mockResolvedValue({
    ...history,
    items: history.items.map((item) => ({ ...item, withdrawn: true })),
  });
  const result = await readBooklet(
    { source, version, offer, packet: packageFixture() },
    signal(),
  );
  expect(result.signature).toBeNull();
  expect(result.publication).toBeNull();
});
it("rejects cross-workspace, cross-offer and cancelled results", async () => {
  const source = bookletSource();
  await expect(
    readBooklet(
      {
        source,
        version: { ...version, workspace_id: crypto.randomUUID() },
        offer,
        packet: null,
      },
      signal(),
    ),
  ).rejects.toThrow();
  vi.spyOn(source.gateway, "campaignStatus").mockResolvedValue({
    ...(await source.gateway.campaignStatus(offer.id)),
    receipt: { ...offer, id: crypto.randomUUID() },
  });
  await expect(
    readBooklet({ source, version, offer, packet: null }, signal()),
  ).rejects.toThrow();
  const controller = new AbortController();
  controller.abort();
  await expect(
    readBooklet(
      { source: bookletSource(), version, offer, packet: null },
      controller.signal,
    ),
  ).rejects.toThrow();
});
