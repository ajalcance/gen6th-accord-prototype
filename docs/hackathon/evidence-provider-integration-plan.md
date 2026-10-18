# Evidence-provider integration preparation — 2026-10-03

**2026-10-05 update:** evidence intake, explicit asset enrollment and approved public/passport
issuance source are recorded in [S8–S10](evidence-assets-public-passport-slices.md). Source and
QR third-party notice belong in the package inventory; provider/SQL/publication acceptance
remains pending. This update supersedes older claims that these HTTP/UI capabilities are absent.

**Status: proposed next implementation scope; no provider selected or activated.**
Prepared under the 21:07:44–23:07:44 Manila review/preparation window. Existing ADR-0031
remains the governing quarantine decision. This plan does not replace it or approve a provider,
installation, credentials, routes, persistent migrations, real uploads or scheduled deletion.

## Existing interfaces and enforcement

| Interface | Current source | Existing service requirement |
| --- | --- | --- |
| Content inspection | `ContentInspector.inspect(bytes) -> Inspection`, `personas/evidence_service.py` | Full bounded decoding plus malware inspection; timeout/error never means clean |
| Inspection result | `Inspection`, `personas/evidence_contracts.py` | Exact digest/length/type/time; engine/definitions metadata; clean or rejected |
| Key wrapping | `KeyWrapper.wrap/unwrap`, `personas/evidence_crypto.py` | Authenticated context binding; no unknown/retired/context-mismatched fallback |
| Retention | `RetentionGate.may_purge(workspace_id, evidence_id) -> bool` | Only literal True allows expired ciphertext deletion; outage/ambiguity deny |
| Intake | `collect/enqueue`, `personas/evidence_service.py` | Creator/owner authorization before stream consumption; exact declared size/digest; current version for new evidence |
| Private read/purge | `read_evidence/purge_expired`, same service | Owner-only clean/unexpired read; observation commits before plaintext release; expiry plus retention authorization for purge |

Current intake allows **1 byte–10 MiB** and PNG/JPEG/plain text, has a **30-second** collection
deadline and stores encrypted payloads with a **seven-day** expiry. Key wrap/read/retention
operations use **10-second** service deadlines; inspection uses **30 seconds** including decryption.
These are existing code limits, not newly approved provider capacities. Transaction scope currently
includes provider waits. Provider concurrency, memory/CPU bounds and trusted definition freshness
are not certified by a timeout alone.

AES-GCM uses a fresh 256-bit data key and nonce. Authenticated context includes workspace,
version, evidence ID and digest. No default key loader, software KMS, malware/decoder provider,
retention source or cleanup worker exists. Clean inspection stays quarantine metadata, not
rights, approved campaign assets, signing, public visibility or permanent retention.

## Proposed bounded implementation unit

After owner approval of this scope and concrete provider decisions, implement one provider
adapter at a time behind the existing interfaces, with no application mounting or automatic
cleanup. Start with content inspection because a valid content-type claim is not decoded-media
or malware proof. Reuse the current contracts instead of adding a duplicate provider API.

Before selecting or installing software, prepare a specific candidate review with primary
documentation, exact dependency/artifact versions, license, maintenance, definition/update path,
platform requirements and demonstrated resource bounds. No candidate recommendation or external
provider compatibility is asserted by this source review. Install approval remains per package.

The inspection adapter must combine all required checks before returning clean. A partial
decoder result or an available engine with stale/unknown definitions cannot become clean.
Network/API result data must be validated before constructing a trusted `Inspection`.
Propose explicit definition-age and decoded-image/text bounds for owner review; do not silently
choose thresholds or loosen the 10 MiB/media boundary to accommodate a provider.

The adapter configuration and tests remain disconnected from application bootstrap. A required
provider's absence must be explicit unavailability. Test doubles belong in tests and cannot
be runtime fallback providers. Any new durable provider/retention/key decision needs its own
ADR and matching security/as-built records before adoption.

## Decisions required before implementation

| Decision | Concrete evidence to prepare | Owner choice |
| --- | --- | --- |
| Decoder and malware engine | Exact versions/license; full PNG/JPEG decoding and bounded text validation; process isolation, definition provenance/freshness and update failures | Approve the specific tools, limits and package installation |
| Wrapping-key custody | Context-authenticated wrap/unwrap proof, allowed key IDs, rotation/retirement/recovery and availability; separate from signing keys | Local/provider choice and operating responsibility; no pasted secret |
| Retention authority | Hold/retention source, expiry/hold race behavior, unavailable response and durable purge authorization/audit | Approve retention semantics and authoritative source |
| Execution/observation | Resource/concurrency budget, cancellation/timeout cleanup, private-safe logs and failure observations | Approve adapter operation; worker/queue activation remains separate |
| Real evidence catalogue | Permitted originals/derivatives, consent/license/provenance and private/public distinction | Approve inventory; never substitute quarantine for fixture campaign assets |

These choices can be reviewed separately. The current renewal authorizes preparing them;
it does not grant keys, choose a vendor, enable paid services or approve every future module.

## Acceptance and fault matrix

Existing tests cover service contracts using synthetic providers. New tests must prove the
selected real adapter boundary and provider behavior rather than duplicate those assertions.

| Boundary | Existing proof | Additional provider acceptance needed |
| --- | --- | --- |
| Intake | `test_private_evidence_contracts.py`: chunked length/digest/authority-field rejection; `test_private_evidence_failures.py`: foreign tenant denied before stream consumption | Real adapter receives only bounded collected bytes; metadata/file names never control storage or commands |
| Decode | Declared media/digest/length/type/time bind to inspection | Valid tiny originals; truncated/malformed media, MIME disagreement, excessive decoded dimensions/frames, invalid text and exhausted resource budgets |
| Malware | Synthetic rejected inspection cannot be read | Selected engine's documented benign detection fixture in isolated tests; engine outage, partial response, unknown verdict and stale/unavailable definitions deny clean |
| Time/cancellation | Service deadlines exist | Provider hang/cancellation cleans up its work and resources, produces no clean inspection or released plaintext, and does not leave a permissive fallback |
| Wrapping | Real AES-GCM tests: fresh keys/nonces, ciphertext/context substitution and missing wrapper failures | Concrete wrapper authenticates context; unknown/retired ID, malformed response, outage and context mismatch fail; no plaintext key in records/logs |
| Inspection metadata | `test_private_evidence_failures.py`: mismatched digest/size/type/time refused | Raw provider responses validate exact bytes and trusted engine/definition metadata; HTTP success alone is insufficient |
| Retention | `test_private_evidence_retention.py`: hold/outage deny, expired payload-only purge, immutable rows and tenant RLS | Concrete authoritative hold/retention response and race behavior; malformed/unknown state denies; scheduled cleanup absent |
| Persistence/observation | Owner SQL proof for encrypted storage, immutable metadata and tracked service actions | Source-bound SQL journey with the selected adapter test seam; provider faults do not commit clean state or delete held ciphertext |
| Privacy | Snapshots omit keys/bytes/addresses; access is creator/owner-scoped | Provider request/logging captures verify no cross-tenant bytes, tokens, plaintext keys or unnecessary filenames; review any external data transfer explicitly |

Service/provider tests do not prove authenticated HTTP, live identity or rendered upload UX.
Those require separate session/origin/CSRF/ingress review and activation approval. Benchmarks
need the approved asset inventory and measured results; no original/matching accuracy claim is made.

## Exit conditions for an approved adapter slice

1. Provider identity, maintenance/license, resource limits and private-data handling are owner-reviewed.
2. Adapter implements the existing interface and refuses missing/failed/ambiguous configuration.
3. Concrete provider success/fault tests pass; synthetic integration, real-service SQL and provider
   acceptance are reported separately. Source fingerprints and complete gates match changed bytes.
4. No route, provider bootstrap, key credential, worker schedule, real upload or public projection
   is enabled by the adapter-only slice. Record implementation truth and remaining activation steps.
5. Update PLAN/LESSONS/as-built/CHANGELOG/SECURITY and a decision ADR where required; obtain
   revision-bound PR/CI and owner review. A failed gate is fixed at its underlying cause.

The next actionable approval is for a specific adapter/tool proposal with these tests and
limits, after current PR/security and rendered-review prerequisites are addressed.
