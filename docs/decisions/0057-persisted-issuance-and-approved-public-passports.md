# ADR-0057 — Persisted issuance and approved public passports

- **Status:** Accepted for source implementation; publication serving disabled pending activation.
- **Date:** 2026-10-05
- **Context:** S6 prepared signing and integrity verification. The owner now authorized remaining
  MVP modules, including public field approval, discoverable issuance history and replay rules.

## Decision

Persist private signed issuance once per workspace/campaign/acceptance. Under existing campaign
and persona locks, revalidate permission and reference bindings before returning committed bytes.
A committed retry reuses the package without signing again. A failure before commit can still
repeat provider cost; no exactly-once external signing claim is made.

Create a separate signed public projection only after explicit owner approval of allowlisted
fields: name, biography, human contribution, AI disclosure, production title, purpose,
conditions and optional inspected portrait thumbnail digest. Name and AI disclosure are required.
Public identifiers disclose no general workspace access. Retained trusted platform keys verify
the stored grant; uploaded keys are never trusted. Private packages, party identifiers, original
images, analysis bytes and evidence remain outside the public contract.

Expose approval preview, history, share link, local QR, downloaded package verification and
append-only withdrawal in the frontend. Anonymous reads return only approved fields and coarse
fresh eligibility, distinct from integrity. Eligibility applies to the named scope/recipient,
not to every viewer. Expired/revoked use retains historical public disclosure until withdrawal.
Withdrawal denies future page, verification and thumbnail reads; downloaded copies persist.
An old withdrawn approval intent cannot resurrect publication.

Use existing Ed25519/KMS adapters, no new dependency. Keep public serving false by default,
with startup denial for activation without trusted runtime keys. Prepare forced tenant RLS,
immutable tables and confined grants in migration 0016. Owner/CI SQL, actual keys, anonymous
ingress rate/cost limits, browser/QR scan and publication consent remain activation gates.

## Consequences

The public package is a creator statement with verifiable platform integrity, not legal
recognition, unique identity proof or a reuse licence. Public GETs emit minimal server events;
retention/capacity and anonymous ingress protection require operational acceptance.
See [source and acceptance record](../hackathon/evidence-assets-public-passport-slices.md).
