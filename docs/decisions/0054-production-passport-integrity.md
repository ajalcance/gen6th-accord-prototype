# ADR-0054: Production scopes and passport integrity

- Status: Proposed for human PR review; S6 source prepared under the approved slice plan
- Date: 2026-10-05
- Supersedes: None; extends ADRs 0026 and 0048–0053

## Context

A continuing synthetic performer may play different characters in different films. Similarity,
an independent review and creator claims cannot authorize unspecified episodes or adaptations.
A signed export must remain verifiable after expiry or revocation without restoring permission.

## Decision

Reuse the existing immutable exact-version campaign offer, assets, independent review, named
recipient, bounded duration, recipient decision and final owner revocation. Add optional production
title, named episode/installment, character/role, permitted adaptation and at most eight distinct
submitted consent/claim evidence IDs. Performer identity remains the persona/version; the role
belongs to the production offer. New episodes, roles, recipients or conditions require a new offer.

Production metadata is stored on the immutable offer as bounded nullable JSONB. Migration
0014production preserves existing rows and their RLS/immutability. Omit absent production from
serialization to preserve legacy exact-retry fingerprints. Downgrade requires an all-tenant role,
locks offers, and refuses to drop populated production scopes. Migration execution is owner-gated.

Referenced evidence must belong to the owner, studio and exact version, have a clean inspection,
an unexpired metadata window and retained encrypted payload. Recheck availability for acceptance,
current status and export. Quarantine, rejection, expiry or unavailable payload blocks referenced
use; clean scanning never verifies consent or rights. An empty optional reference list is an
explicit evidence gap. The existing seven-day evidence lifecycle limits this prototype; durable
consent attestations and policy-controlled renewal require future design. No plaintext is shared.

Expose owner-only bounded exact-version asset catalogue reads so connected creators can select
existing production assets. This reads the server-managed catalogue; it creates no asset ingestion
or grant path. Empty/overflow/denied states stay explicit; private evidence cannot replace assets.

An injected signing runtime exports only currently eligible accepted production scopes with an
approved reference set. The server constructs a passport projection from immutable version,
campaign/asset hashes, acceptance ID and capture provenance/reference hashes. Reviewer/recipient
comments, private evidence bytes, investigations, vectors, ciphertext, keys and URLs are excluded.
Creator statements and submitted reference IDs carry an explicit unverified-claims label.
The UI requires explicit confirmation before requesting the portable package.

Sign domain-separated canonical JSON with Ed25519 using existing cryptography. This format is
versioned sorted ASCII JSON with compact separators, finite numbers and a fixed domain prefix;
it is not an assertion of JCS, transparency-log or timestamp assurance. Object ordering/outer JSON
whitespace are transport details; altered signed values fail verification. Trust keys are injected
server configuration, never keys/URLs from the package. Unknown or withdrawn trust keys fail closed.

Prepare a Google Cloud KMS EC_SIGN_ED25519 software-key-version adapter with explicit workload
transport, immutable validated resource, raw data, CRC32C request/response checks and the existing
bounded no-redirect transport. Verify the returned signature against the configured trusted public
key before release. No key creation, credential discovery, cloud call, signing activation or cost
is authorized by source preparation. Wire references:
[algorithms](https://docs.cloud.google.com/kms/docs/algorithms),
[asymmetricSign](https://docs.cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys.cryptoKeyVersions/asymmetricSign).

Export authorizes parties before signing, uses the persona lock and rechecks human membership
and current permission after the bounded signer call. Stateless export requests may produce new
issue times and repeat signing cost on explicit retry; no exactly-once issuance or durable export
history is claimed. S7 owns delivery/cost/recovery integration and key lifecycle acceptance.

Verification requires a current party session before package consumption and current permission
queries. Reject duplicate JSON keys, oversized/deeply malformed input and authoritative extras.
Verify the signature before interpreting payload claims, then bind the package to saved version,
offer/assets, ordered approved capture references and an actual historical acceptance ID. Only a
valid bound package returns freshly computed permission. Expired/revoked/stale permission can
coexist with valid integrity; an altered/untrusted/mismatched package never grants use.

All four private passport routes use existing server-observation coverage, without auditing
uploaded contents as server facts. The frontend exposes catalogue loading, production fields,
status/history, adapter availability, export/download, JSON file/paste verification and altered
results. Context changes/access loss clear results; late requests/file reads are ignored and
download URLs revoked. There is no public verification route or external publishing action.

## Consequences and acceptance

Integrity is reproducible with ephemeral test keys while live issuance remains unavailable by
default. Studio permission and legal acceptance remain separate. Reviewed migration and source
checks do not certify PostgreSQL enforcement, real KMS key lifecycle, actual Google processing,
rendered accessibility or owner-reviewed PR/CI. See [S6 evidence](../hackathon/production-passport-slice.md).
