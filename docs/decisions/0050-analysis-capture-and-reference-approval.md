# ADR-0050 — Dedicated analysis capture and version-bound reference approval

- Status: Accepted for source implementation; migration/provider/live acceptance pending
- Date: 2026-10-05
- Context: Owner approved the capture/search plan and requested the next slice, S2.

## Decision

Extend the isolated decoder protocol to return two independent, orientation-corrected,
metadata-free RGBA PNG images: the existing maximum-320px display thumbnail and a
maximum-1024px analysis derivative. Never upscale. Keep the 8-million-pixel source bound,
5-second CPU/512-MiB Linux worker limit, two-worker concurrency and 10-second wall timeout.
Bound the analysis output to 5 MiB; scan original, thumbnail and analysis before encryption.

Store analysis pixels in a separate immutable encrypted capture row. Bind workspace, portrait,
source/analysis digests, recipe, decoder release, dimensions/orientation, scanner receipt and
timestamp into authenticated encryption/wrapping context. Record source dimensions/orientation
and normalized dimensions, recipe `rgba-png-1024-v1`, Pillow release and digests as provenance.
This first capture generation is not a face-selection, quality or embedding verdict.

Approve an ordered set of at most eight unique prepared references through the existing
new-version save operation. Initial registration approves its explicitly selected prepared
portrait as the first reference. Later display-photo changes preserve the reference set;
explicit `replace` changes its membership/order, including an empty set. Default `keep` inherits
the preceding version. All references must belong to the writing owner and studio and have
a stored capture. A stage expires after 24 hours unless previously enrolled in the same persona.
Historical bindings and captures remain immutable. Legacy portraits are not silently backfilled.

Use additive migration `0011captures`, forced tenant RLS and the shared immutable trigger.
Prepare confined runtime SELECT/INSERT grants only; do not execute schema/grants or restart
the connected service. Migration approval, provider activation and retention are owner gates.

Expose private capture metadata queries and exact-version reference thumbnails. Upload metadata
is owner-only; version metadata/thumbnails require current studio membership and binding.
Never return original/analysis bytes, nonce, ciphertext or wrapping keys. Reuse registered
portrait read/bound actions and the existing new-version event/replay transaction. Default
reference `keep` is omitted from serialization to preserve old request fingerprints.

Show staged capture status after Scan and saved provenance/reference inspection in Records.
Require explicit Add checked reference and confirmed Save reference version. Removal/reordering
creates a new version, and exact retries preserve the full ordered intent. The thumbnail remains
the display image; analysis is explicitly shown as prepared, with recognition not run.
Extend S1 exact search to both primary and approved reference history, without enrolling queries.

## Consequences and verification

S3 can consume provenance-bound analysis pixels rather than a low-resolution thumbnail. Its
crop, face-quality and model compatibility contracts remain future work; no Google calls or
recognition accuracy are established by S2. Durable ready captures and synchronous pending/
failure/retry states exist; durable queued model jobs belong to S3/S7.

Real Pillow and cryptographic tests, private ASGI/contract checks, offline migration rendering
and frontend transport/state tests supplement owner/CI PostgreSQL tests for ownership,
atomicity, expiry, immutable version history and exact search. See the
[source and acceptance record](../hackathon/analysis-capture-reference-slice.md).
