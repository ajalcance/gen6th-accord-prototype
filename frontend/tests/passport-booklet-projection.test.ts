import { expect, it } from "vitest";
import {
  bookletMachineLine,
  bookletPublication,
  bookletReference,
  bookletShare,
  bookletSignature,
} from "../lib/passport-booklet";
import { offer, packageFixture, version } from "./passport-fixtures";
import { bookletPublicationFixture } from "./booklet-fixtures";

it("derives references only from the selected offer and labels absence", () => {
  expect(bookletReference(null)).toBe("Not assigned");
  expect(bookletReference(offer)).toBe(
    `AC-${offer.id.replaceAll("-", "").slice(-8).toUpperCase()}`,
  );
  expect(bookletReference({ ...offer })).toBe(bookletReference(offer));
  expect(
    bookletReference({ ...offer, id: "00000000-0000-4000-8000-000000000096" }),
  ).not.toBe(bookletReference(offer));
  expect(bookletMachineLine(version, null)).toContain("REGISTRATION::NO_OFFER");
});
it("binds private issue time, real key tail and signed references to exact saved records", () => {
  const packet = packageFixture();
  packet.key_id =
    "projects/fictional/locations/global/keyRings/demo/cryptoKeys/demo/cryptoKeyVersions/7";
  expect(bookletSignature(packet, version, offer)).toEqual({
    key: "cryptoKeyVersions/7",
    issued: packet.payload.issued_at,
    references: 1,
  });
  expect(() =>
    bookletSignature(
      packet,
      { ...version, revision: version.revision + 1 },
      offer,
    ),
  ).toThrow();
  expect(() =>
    bookletSignature(packet, version, { ...offer, id: crypto.randomUUID() }),
  ).toThrow();
  expect(() =>
    bookletSignature(
      { ...packet, payload: { ...packet.payload, issued_at: "not-a-date" } },
      version,
      offer,
    ),
  ).toThrow();
});
it("rejects public/private format confusion and mismatched public bindings", () => {
  const receipt = bookletPublicationFixture();
  expect(bookletPublication(receipt, version, offer)?.path).toBe(receipt.path);
  expect(() => bookletSignature(receipt.package, version, offer)).toThrow();
  expect(() =>
    bookletPublication(
      { ...receipt, package: packageFixture() },
      version,
      offer,
    ),
  ).toThrow();
  expect(
    bookletPublication(
      receipt,
      { ...version, revision: version.revision + 1 },
      offer,
    ),
  ).toBeNull();
  expect(
    bookletPublication(receipt, version, {
      ...offer,
      scope: { ...offer.scope, ends_at: "2027-01-01T00:00:00Z" },
    }),
  ).toBeNull();
  expect(() =>
    bookletPublication(
      { ...receipt, path: "https://example.invalid/p/foreign" },
      version,
      offer,
    ),
  ).toThrow();
});
it("encodes only an approved same-origin public URL and fails closed for missing/oversized URLs", () => {
  const path = bookletPublicationFixture().path;
  expect(
    bookletShare(path, "https://accord.example")?.modules.length,
  ).toBeGreaterThan(0);
  expect(bookletShare(null, "https://accord.example")).toBeNull();
  expect(bookletShare(path, "")).toBeNull();
  expect(
    bookletShare("https://other.example/p/elsewhere", "https://accord.example"),
  ).toBeNull();
  expect(bookletShare(path, `https://${"x".repeat(190)}.example`)).toBeNull();
});
