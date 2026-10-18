# S6 — production clearance and passport integrity

Owner authorized implementation on October 5, 2026. Implements
[ADR-0054](../decisions/0054-production-passport-integrity.md) and
[approved slices](capture-search-slices.md). Backend and frontend source are prepared;
default signing/verification runtime remains unavailable.

## Studio journey and capability coverage

1. Records → prepare action → Offer campaign. Load the exact-version production asset catalogue
   if this connection has no injected catalogue. Select only named asset hashes and the latest
   independent approval, recipient, purpose, conditions and timezone-aware duration.
2. Select “Name a production and role.” Enter production, episode/installment, character and
   permitted appearance/adaptation. The continuing performer remains the saved persona/version.
   Optionally supply consent:ID or claim:ID references from the owner's exact-version evidence.
   Confirm the bounded offer and sharing of production/reference IDs before recording it.
3. The existing named-recipient decision workflow accepts or requests changes; the owner can
   revoke. Records → Campaigns shows production scope, current blocking reasons and append-only
   decision history. New episode/role/use does not extend an earlier offer.
4. Records → saved version → Passport. Choose a production offer, inspect named use and refresh
   current permission. Configuration availability is visible separately from permission.
5. With accepted current permission, approved references and configured keys, explicitly confirm
   portable-package sharing and prepare/download signed JSON. Missing providers cannot yield an
   unsigned “success.” S10 now persists issuance per acceptance: a committed retry returns the
   original trusted package without signing again; a precommit failure can repeat cost.
   [S8–S10 record](evidence-assets-public-passport-slices.md) also adds explicit asset enrollment
   and separately approved public projection/history/withdrawal.
6. Paste or choose a bounded passport JSON file; explicitly verify it for the selected production.
   Inspect integrity and fresh permission separately. Alter a signed value to exercise rejection.
   Valid signatures on revoked/expired scopes still show current use blocked.

New routes under `/api/workspaces/{workspace_id}/personas/passports`:

| POST route | Server capability | Frontend exposure |
|---|---|---|
| `/assets` | Owner-only exact-version catalogue, max 20; no upload/grant | Load production assets, empty/error/retry/cancel |
| `/readiness` | Configured signer/trust-key availability, no live probe | Availability and disabled controls |
| `/export` | Current accepted production + approved-reference projection/signature | Sharing confirmation, manual prepare, JSON download/inspection |
| `/verify` | Trusted signature, immutable binding, current permission | File/paste, manual verification, altered/untrusted/mismatched result |

Existing offer, decision, discovery, status and history routes carry the production extension.
Missing optional production remains a legacy campaign; no automatic conversion or fingerprint
rewrite occurs. New production scope participates in exact-intent retry equality.

## Evidence, privacy and Google integration

Private consent/claim references are metadata associations, not legal-rights determinations.
The server checks owner/studio/version, clean inspection, expiry and retained encrypted payload
without decrypting or sharing it. Referenced evidence availability is recomputed for acceptance,
current permission and export. The existing seven-day private evidence lifecycle can block a
longer production window; durable attestations/renewal are future work. Empty references remain
visible evidence gaps rather than invented approvals.

The portable projection contains version/creator statements, exact campaign scope and assets,
review/acceptance IDs and approved source/analysis reference hashes with capture provenance.
It contains no private evidence pixels/text, reviewer/recipient comments, vectors, investigation
packets, ciphertext, encryption material or external URLs. Signed creator statements remain
explicitly unverified. File integrity covers canonical semantic contents, not raw JSON whitespace.

Ed25519 signs `accord-persona-passport-v1` plus a zero-byte domain separator and sorted compact
ASCII JSON. Uploaded envelopes cannot choose algorithms, public keys or trust endpoints. Unknown
trust keys, bad signatures, invalid schema and saved-record binding mismatches are distinct
results; invalid packages disclose no fresh permission record. Verification is private to current
offer parties; the pure trust adapter also supports independently configured verification.

Google KMS uses an explicit EC_SIGN_ED25519 software key version, raw canonical data and
CRC32C transport checks; the server independently verifies the signature before responding.
The existing Google transport uses injected workload tokens, no credential discovery/redirects,
20-second network timeout and bounded responses. Signer call bound is 25 seconds; client requests
use 30 seconds, within the existing proxy budget. This is a prepared adapter, not an executed
Google/KMS acceptance. [Google wire contract](https://docs.cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys.cryptoKeyVersions/asymmetricSign).

Package metadata consumption is capped at 64 KiB and five seconds after trusted session and
membership checks. Server duplicate-key rejection avoids ambiguous incoming JSON. Frontend
selection previews/pastes only; clicking Verify sends the bounded parsed semantic package.
Access loss/context changes remove responses and object URLs; late reads/results are ignored.

Migration `0014production` adds bounded nullable JSONB to the already immutable/RLS-protected
offer. Downgrade requires all-tenant migration authority, locks offers and refuses populated scopes.
Existing table-level SELECT/INSERT privileges cover the new column; no new runtime grant is added.
Earlier grant scripts require their exact intermediate migration heads: review/apply those at
their named revisions before advancing. Do not run an old exact-head script against 0014.
Migration, keys, workload permissions and runtime assembly remain separate owner activation gates.

Atomic observations use existing `persona.workflow_observed` for catalogue/export/verification
and `persona.workspace_observed` for configuration/input observation. Existing emission/detection/
audit/compliance coverage applies. Observation events contain identifiers only; an uploaded
statement is never copied into the tamper-evident chain as a server-authored claim.

## Validation and remaining acceptance

October 5 source verification:

- 64 S6 backend tests pass, including real in-memory Ed25519 signing/tampering, authorization,
  post-provider permission checks, bounded HTTP contracts, Google transport and offline migration.
  The broader S1-S6/spine selection passes 222 tests; no PostgreSQL execution is implied.
- 413 frontend unit tests across 45 files pass, including 22 S6 cases. Existing isolated
  ASGI-to-UI integration passes 15 tests across two files after updating the status-label assertion.
- Backend Ruff/Black (292 files), mypy (278 files) and Bandit pass. Frontend lint, formatting,
  TypeScript, production build and bundle budget pass: shared bundle 166.4 kB gzip / 250 kB.
- Repeated `make check` passes preflight, 776 guard tests (18 skipped), policy/harness and backend
  static checks, then fails at pip-audit's temporary pip-upgrade bootstrap. The complete gate,
  dependency audit, full SQL/coverage and later Trust/frontend stages remain incomplete.
- `make frontend` passes lint/format/types, then npm audit fails with registry DNS `ENOTFOUND`.
  Independent test/build success does not substitute for a successful dependency audit.
- `make dod-check` passes with 56 ADRs / 154 standards. S6 file/function bounds and whitespace
  checks pass. Seven new PostgreSQL cases collect successfully and remain unexecuted.

Owner/CI SQL tests cover production retry/binding, encrypted evidence availability, party isolation,
actual signatures, tamper rejection, revocation and immutable scope protection. Collection is not
SQL execution. Default bootstrap injects no signer or trust registry; live activation is S7 work.

Remaining acceptance: reviewed migrations/roles, actual scanner/Linux/Redis/Google providers,
permitted corpus/calibration, KMS key-version/public-trust lifecycle and costs, restart/replay,
rendered creator/independent-reviewer/production/passport journey, owner PR and revision-bound CI.
No installs, private configuration, migration/grant execution, runtime restart, cloud/key activation,
real-key signing, publication or Git writes occur during this source slice. S7 is the next slice.
