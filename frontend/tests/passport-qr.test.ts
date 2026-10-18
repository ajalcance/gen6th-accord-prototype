import { createHash } from "node:crypto";
import { expect, it } from "vitest";
import { passportQr } from "../lib/passport-qr";

// Independent ReportLab QR8bitByte / version 8 / L / mask 0 fixtures from the bundled runtime.
it.each([
  [
    "https://accord.example/p/11111111-1111-4111-8111-111111111111/22222222-2222-4222-8222-222222222222",
    "64cf8b38ae16da001e965faf92d12b57600b1e774c8d46b422cdc0523c014331",
  ],
  [
    "a".repeat(192),
    "fc666921a21d185de677d1969e435c0c43d78215923c9fb4f20737f971e44f7d",
  ],
])("matches an independent QR matrix for %s", (value, digest) => {
  const cells = passportQr(value);
  expect(cells.length).toBe(49);
  expect(
    createHash("sha256")
      .update(new Uint8Array(cells.flat().map(Number)))
      .digest("hex"),
  ).toBe(digest);
});
it.each(["", "a".repeat(193), "synthetic😀"])(
  "rejects unsupported QR payload %s",
  (value) => expect(() => passportQr(value)).toThrow(),
);
