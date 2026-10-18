# Performer identity, credits and ORCID-inspired development register

Owner approval: 2026-10-06, Asia/Manila. Decision: [ADR-0060](../decisions/0060-attributed-performer-identity-and-credits.md).
The owner approved the recommended MVP and requested retention of every comparison item for
future development. This is an Accord adaptation; no ORCID account linking or API integration.

The October 11 [L1–L10 lifecycle extension](performer-lifecycle.md) implements bounded operator,
rights/content assessments and concerns without dropping any O1–O8 acceptance criteria below.

## MVP scope and source truth

- **Persistent identity and provenance:** Record overview displays the existing performer ID,
  workspace scope, submitting account, saved version and receipt time. Renaming does not
  replace the performer ID. Portrait inspection, reference approval, independent review,
  production permission and signature integrity remain separately supported assertions.
- **Aliases and structured credits:** the creator/performer owner records optional aliases,
  contributor type/name/role and optional account/evidence reference on the current version.
  The authenticated named human can deliberately confirm their own credited role. A typed
  account reference is only a nomination; organization credits remain creator-declared.
- **Production history:** the record's Production history tab browses authorized offers for
  the selected version with production/episode/role and asset counts. Opening an entry reads
  its current permission and existing receipt history. No actual participation is inferred.

Credit annotations have independent immutable receipts. Existing version reviews and private
or public passport exports do not include/certify them. All credit metadata is visible to
authorized workspace members; private evidence bytes retain their existing owner boundary.
Changing a declaration does not carry confirmations forward. Old annotations/confirmations
remain retained, even though this first read surface returns the latest declaration only.
Historical versions can be read; new declarations/confirmations require the current version.

MVP limits: eight aliases, twelve credits, 10,000 content bytes, 12,288 request bytes. Roles:
design, writing, direction, illustration, source performance and other. Credits are optional,
do not replace required capture contribution/disclosure, and do not grant rights or membership.
No inferred sensitive attributes, face-derived identity, automatic public sharing or emails.

## Complete feature register

| ID | ORCID practice to adapt | MVP source coverage | Future development and exit criteria |
|---|---|---|---|
| O1 | Persistent identifier independent of name | Existing performer UUID surfaced with copy, version and workspace scope | Opt-in stable resolver and issuer/workspace namespace; name/alias history. Rename/version changes preserve identity; withdrawn/private records disclose no unauthorized metadata. A public resolver must not expose private account IDs. |
| O2 | Authenticated association instead of trusting typed IDs | Only a named workspace human confirms their own role; creator declarations stay distinct | Authorized account directory/picker, invited claim-and-accept flow, revocation/correction of association and verified organization representatives. Forged/manual associations never receive an authenticated badge; membership loss, stale declarations and cross-workspace requests deny. |
| O3 | Provenance and claim-specific trust markers | Source account/time, creator-declared vs contributor-confirmed, existing separate review/permission/signature surfaces | Claim-level source/issuer, verification method, reviewer and exact annotated revision. Corrections/withdrawals preserve history; a review binds the declaration ID it examined. Never use one blanket verified badge for unrelated claims. |
| O4 | Record-owner visibility and permission control | Workspace-only annotation metadata; linked evidence remains private; existing explicit public passport allowlist remains | Field/evidence-level scopes, named recipients, expiry/revocation, opt-in catalogue sharing and public projection preview. Unauthorized reads/searches/exports deny; withdrawn grants invalidate cached views. Originals and face representations are excluded from public projections. |
| O5 | Structured works, roles and production history | Structured contributor roles and bounded exact-version production offer/scope/asset/permission history | Explicit production participation attestations with production/episode/role, date, recipient confirmation and evidence; cancellation/correction. Group externally identified works only through explicit relations. Permission acceptance never creates an appeared-in claim; historical permissions remain distinguishable from current use. |
| O6 | Trusted individuals and organizations with revocable access | Existing workspace roles only; no new delegates | Viewable least-privilege grants for named delegates/organizations with permitted actions, expiry and owner revocation. Recheck grants at execution and invalidate stale sessions/views. A delegate cannot self-escalate, transfer ownership or authorize publication outside its grant. |
| O7 | Import-assisted review before adding claims | Manual structured entry and metadata evidence picker; no import or automatic claim generation | Bounded schema-validated import preview, source/issuer attribution, duplicate detection and explicit per-item confirmation. External identifiers/JSON remain proposed claims until accepted; no URL/model execution from imported content. Separately version annotated exports/signatures; older passports must not acquire later credits. |
| O8 | Duplicate correction and concern resolution | No merge, transfer, dispute decision or global uniqueness claim | Human-reviewed duplicate/correction/concern cases with attributed evidence, parties' responses and resolution history. Preserve original immutable IDs/versions with explicit aliases/redirects where authorized. A similarity result cannot merge identities or decide ownership; no silent historical erase. |

Every row is a retained roadmap item, not an implemented promise. Direction is approved; each
future slice requires a concrete design, tests and activation decision. No absent row is
implicitly waived. Future scoped in-app notifications can support O2/O6/O8; delivery permissions,
recipient preferences and retention must be designed before any outbound message capability.

## Recommended sequencing

1. Finish current source checks and owner visual review; retain recognition/runtime acceptance
   as independent unfinished gates. Owner-approved disposable SQL and real-session tests must
   pass before enabling credits on an existing installation.
2. Improve O2 account selection and contributor correction/history, then O3 declaration-bound
   review. Show exactly what a confirmation or reviewer examined.
3. O5 actual production attestations, then O4 granular sharing/public projection and O1 resolver.
   Tie export inclusion to explicit consent and exact annotated revisions.
4. O6 delegates/organization authority, O7 import/interoperable exports and O8 human case handling.
   Broader adoption must retain tenant isolation and original historical identifiers.

## Source map and activation requirements

Backend: `credit_contracts`, `credit_models`, `credit_repository`, `credit_service`,
`credit_intent`, `credit_http`. Three session-gated POST routes under
`/api/workspaces/{workspace_id}/personas/credits/`: `read`, `save`, `confirm`.
They authorize membership before bounded body parsing and reauthorize in tracked transactions.
Actor attribution comes from the verified session. Content cannot supply a confirmed state,
actor identity, visibility switch or review outcome. Exact retry fingerprints, owner/current-version
checks, compare-and-swap declaration IDs and scoped confirmation receipts constrain mutation.

Frontend: `persona-credits.ts`, performer identity/credits, credit editor/fields/evidence picker,
credit state and production history components. Existing in-memory draft, cancellation,
access-loss and uncertain-outcome recovery apply; no persistent browser store of server receipts.

Prepared owner-only artifacts: migration `0017credits` (after `0016passports`) and
`deploy/accord-credit-runtime-grants.sql`. The latter checks migration head and confined
`accord_runtime` flags, then grants SELECT/INSERT on only the two new tables. Migration enforces
composite scope foreign keys, replay/slot uniqueness, forced tenant RLS and immutable history.
Rollback requires an all-tenant migration role and refuses any populated credit history.

**Default disabled:** `PERSONA_CREDITS_ENABLED=false`. Current frontend can display an explicit
unavailable state against an older/disabled backend. Prepared source is not live capability.
Before activation the owner must separately authorize schema/grants and process configuration,
verify disposable PostgreSQL migration/RLS/immutability and role confinement, then test real
creator/contributor sessions, stale replacement, revocation and workspace isolation. No keys,
Google call, package install, server restart or production migration was performed here.

## Validation record

Current source checks, 2026-10-06:

- 34 focused backend cases pass: credit contracts/service/synthetic HTTP, frozen migration
  rendering and existing full persona migration SQL rendering. Another 17 spine coverage
  cases pass for route telemetry/detection/audit/compliance registration.
- All 497 frontend tests pass with two workers, including 13 new credit/production cases.
  The initial concurrent run had timing failures; the rerun retained every assertion/time limit.
  Current isolated synthetic ASGI integration rerun passes 11 of 17 cases; six still time out
  around bridge startup/loading or mutation waits. Cause remains unresolved; do not claim full
  integration acceptance or raise time limits to conceal it. A standalone synthetic runtime
  bridge returned HTTP 200 in 3,188 ms; that narrow observation does not close the failures.
- Six new disposable PostgreSQL cases collect only: declaration/confirmation replay and
  replacement, two nonowner denials, two immutable-table cases and forced tenant RLS.
  Existing migration parity/protection tests include the new tables dynamically. Actual
  migrations, role/RLS, concurrency, live sessions and rendered acceptance remain open.
- Ruff/Black/mypy/Bandit pass; mypy inspects 348 source files. Frontend ESLint, Prettier and
  TypeScript pass. Isolated Next production build passes without touching the owner's preview;
  shared bundle is 167.0 kB gzipped against the unchanged 250 kB budget.
- Semgrep reports zero findings, including an explicit scan of all 14 new feature code files.
  Gitleaks reports no leaks in backend source, frontend app/lib or deployment artifacts.
  New feature files/functions stay within the 400/50-line caps.
- `make check` passes preflight, 776 guard cases (18 skipped), policy, harness and backend
  lint/types/Bandit, then stops at pip-audit's temporary pip bootstrap failure. Frontend npm
  audit independently fails DNS resolution for registry.npmjs.org. No audit was bypassed;
  trust/frontend/docs-site/full backend SQL stages are not reached by the full gate.
- `make dod-check` passes as-built/doc consistency, production-readiness register and 154
  standards. No full-green, release, recognition accuracy or runtime acceptance claim.

Working-tree source snapshot (documentation/private config/build output excluded): branch
`security/codex-agent-boundary`, HEAD `407a9f4a67611770143198d1f42d605738b01530`.
Existing mixed changes are preserved; no commit, checkout switch or cleanup occurred.
`source_files=655`, `source_sha256=3470e1897abc84e6bfb9c983a686cab014ec747968347cc53aadadbdd7443ebc`.
Population/algorithm match the [historical handoff](next-session-2026-10-06.md); its earlier hash
is historical, not an instruction to restore source. The new credits grant preparation is
outside that older population: SHA-256 `528fbd37a91c87aa743da19fa4e8c35dc96723372ff4a1990a570dcbe1eef489`.

## ORCID source references for the adaptation

- O1/O3: [ORCID trust](https://info.orcid.org/orcid-trust/),
  [identity assurance limits](https://support.orcid.org/hc/en-us/articles/360006972413-Does-an-ORCID-iD-assure-my-identity).
- O2: [integration best practices](https://info.orcid.org/documentation/integration-best-practices/).
- O3: [trusted record provenance](https://info.orcid.org/how-to-build-a-trusted-automated-orcid-record-key-insights-from-our-latest-id-me-webinar/).
- O4: [visibility settings](https://support.orcid.org/hc/en-us/articles/360006897614-Visibility-settings).
- O5: [grouping works](https://support.orcid.org/hc/en-us/articles/360006894774-Group-multiple-versions-of-the-same-work-together).
- O6: [trusted organizations](https://support.orcid.org/hc/en-us/articles/360006973893-Trusted-organizations),
  [trusted individuals](https://support.orcid.org/hc/en-us/articles/360006973613-Add-a-trusted-individual-to-your-account).
- O7: [identifier-assisted import](https://support.orcid.org/hc/en-us/articles/360022298153-Add-works-using-an-identifier).
- O8: [duplicate identifiers](https://support.orcid.org/hc/en-us/articles/360006896634-I-have-more-than-one-ORCID-iD),
  [record concerns](https://support.orcid.org/hc/en-us/articles/360006972493-What-can-I-do-if-I-have-concerns-about-data-in-the-Registry).

These references motivated the earlier comparison. The register's implementation choices and
exit criteria are Accord proposals, not ORCID compatibility or affiliation claims.
