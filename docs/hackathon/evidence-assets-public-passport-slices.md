# S8–S10 — Evidence, production assets and approved public passports

Owner authorized implementation in the recommended order on October 5, 2026.
ADRs [0056](../decisions/0056-inspected-evidence-and-asset-enrollment.md) and
[0057](../decisions/0057-persisted-issuance-and-approved-public-passports.md) record these decisions.
Source is prepared in the preserved dirty checkout. This record establishes no live activation.

## Studio journey and capability mapping

| Stage | Backend | Frontend |
|---|---|---|
| S8 private evidence | Evidence readiness, raw upload, inspect, content, retention-gated purge | Saved version → private evidence: select → upload → inspect → private download; exact-intent retry, cancellation, saved history |
| S9 asset enrollment | Exact-version clean evidence → explicit permission statement → immutable asset provenance | Separate register action, permission-basis confirmation; refresh production asset catalogue for offers |
| S10 private issuance | Persist package per campaign acceptance; revalidate committed replay without signer call | Existing saved passport prepare/download and verification |
| S10 public passport | Signed allowlist approval, owner history/withdrawal; anonymous projection/verification/approved thumbnail | Field preview/confirmation, approval history, share link/local QR, download, public page, verification, withdrawal |

Evidence routes under `/api/workspaces/{workspace_id}/personas/evidence`:
`/readiness`, `/upload/{version_id}`, `/inspect`, `/content`, `/purge`.
Asset route: `/api/workspaces/{workspace_id}/personas/assets/enroll`.
Owner publication routes: `/api/workspaces/{workspace_id}/personas/publications/approve`,
`/history`, `/unpublish`.
Public routes: `/api/public/passports/{workspace_id}/{publication_id}`, `/verify`, `/portrait`.
Public UI: `/p/{workspace}/{publication}`.

## Private bytes and explicit assets

PNG/JPEG/UTF-8 text are accepted, 1 byte to 10 MiB. PDF, audio and video intake are not implemented.
The existing encrypted quarantine authorizes the owner before body consumption, verifies digest
and declared size, and binds the exact saved version. No original filenames are retained.
Pillow/loopback clamd inspect images; strict UTF-8 and clamd inspect text. Missing workers,
scanner or key provider means unavailable, never clean. Inspection remains an explicit action.
Clean download rechecks role, ownership, expiry, stored length and digest after bounded decryption.
The browser also verifies downloaded length/digest and never puts private bytes in localStorage.

Seven-day expiry prevents reads, not physical deletion. Purge requires an injected trusted
retention/hold gate. None is configured by default; no automatic cleanup service is claimed.
Existing private evidence remains owner-only: independent reviewer plaintext sharing is still
a separate policy/workflow decision, not silently enabled by these modules.

Asset enrollment requires creator ownership, current exact version, clean unexpired evidence
and retained payload. The server chooses the digest. A separate permission statement and
confirmation produce immutable provenance; unique request and version/evidence constraints
prevent duplicate enrollment. A committed same-intent retry returns the original asset.
Catalogue limit is 20 per version. This statement is a claim, not independent rights verification.
Enrollment does not publish private bytes or automatically authorize a production.

## Issuance, public disclosure and integrity

Existing current permission, approved-reference, recipient and scope checks precede private
issuance. Packages are persisted per campaign acceptance. Replay verifies trusted retained
keys and exact reference/version/campaign bindings before returning the original package.
Database locks serialize issuance; provider signing before a failed commit may still cost again.
A new acceptance cycle can have a new issuance.

Public approval is a separate owner/creator action over eight allowed fields. Name and AI
disclosure are mandatory; the inspected thumbnail is optional and unchecked by default.
Scope dates, version revision, approval time and the creator-claims disclaimer also appear.
The projection excludes private export content, recipient/owner IDs, review comments, evidence
and original/analysis bytes. The signing adapter verifies its output against configured trust.
History is owner-only, 20 per page; request fingerprints bind retries.

Anonymous access requires both configured public activation and a stored unwithdrawn grant.
Signature verification and current scoped permission are independent. Altered, unknown-key
or mismatched uploaded packages return no eligibility. Public viewers receive no reuse rights.
A campaign expiry/revocation blocks use while retaining approved historical public fields.
Withdrawal is append-only and denies page, verification and thumbnail serving. Previously
downloaded copies cannot be recalled; withdrawn requests require new explicit approval.

QR generation stays local and adds no dependency. Independent ReportLab matrices validate
the fixed version-8/L encoder at a representative URL and its 192-byte capacity boundary.
Actual phone-camera scanning remains pending. Attribution/licence is retained in
[QR notice](qr-notice.md); reference: [Project Nayuki](https://www.nayuki.io/page/qr-code-generator-library).

## Persistence, providers and spine

Migration `0016passports` follows `0015jobs` and adds asset enrollment, private issuance,
public approval and withdrawal tables, forced tenant RLS, exact evidence/version and
acceptance/workspace/campaign composite bindings (with supporting unique constraints) and immutable
triggers. Downgrade refuses populated tables. Owner-only
`deploy/accord-passport-runtime-grants.sql` grants SELECT/INSERT after head/role checks.
Neither migration nor grants were executed by this implementation.

The still-prepared S5 migration now quotes its investigation-table identifiers consistently
with the offline whole-head protection checks. Policies and immutable triggers retain their behavior;
no checking code or threshold was changed.

`PERSONA_EVIDENCE_ENABLED=false` and `PERSONA_PUBLIC_PASSPORTS_ENABLED=false` remain default.
Evidence reuses the existing encrypted key wrapper and image/scanner runtime. Public enablement
requires configured passport trust at startup. S7 remains the prepared Python KMS/Cloud Tasks
runtime; this work does not activate an alternative Go/PubSub service described in older targets.

Asset registration, issuance, approval, withdrawal and anonymous observation are registered
for telemetry, detection decision, audit and compliance. Mutation events carry bounded identifiers,
not private statements, bytes or browser actor claims. Baseline detection coverage is not proof
of a dedicated misuse detector. Anonymous reads add server events; capacity/retention must be
accepted before exposure.

## Validation and remaining acceptance

Source tests cover upload/session contracts, document inspection faults, exact-byte integrity,
asset enrollment authorization/replay, persisted issuance replay, public field isolation,
tamper/foreign binding, withdrawal and trust failures, frontend manual actions and QR compatibility.
Focused and full-run results are recorded below after the final checks. Mocked-provider/session
tests and SQL collection do not prove deployed SQL/RLS, provider or browser acceptance.

Final October 5 source evidence:

- 85 focused backend tests pass: intake, enrollment, replay, public boundaries, offline migration,
  existing passport orchestration and spine coverage. Ruff/Black/Bandit pass; mypy checks 334 files.
- 459 frontend tests across 53 files pass. All 17 existing isolated HTTP-to-UI integration cases
  also pass; they use synthetic sessions/providers and do not exercise PostgreSQL or live keys.
- ESLint, Prettier, strict TypeScript and the production build pass. Public route is built.
  Shared bundle remains 166.4 kB gzip against a 250 kB budget. Phone/rendered proof remains pending.
- 10 new SQL cases collect, covering explicit enrollment, wrong-version evidence, issuance and
  public replay/concurrency, wrong-campaign acceptance, private-party refusal and withdrawal.
  They were not executed: the existing disposable Docker boundary rejects access in this sandbox.
- Full `make check` with the installed Node 22 passes preflight, 776 guard tests (18 skipped),
  policy/harness and backend static checks, then fails at pip-audit's temporary pip upgrade.
  Backend SQL/coverage and later full-gate stages do not run. No full-green claim.
- `make frontend` passes lint/format/types and stops at npm audit DNS `ENOTFOUND registry.npmjs.org`.
  Tests/build/bundle above ran independently. Both required audits remain in the gate.
- `make dod-check`, whitespace and new backend file/function cap checks pass. Targeted gitleaks
  scans of persona source and frontend libraries find no leaks. Semgrep dangerous-ops scans 259
  targets with 11 applicable rules and no findings; its log is scoped to the project cache.
- No installs, live keys, runtime restart, migration/grant execution, cloud/model calls,
  publication, submission or Git-history changes occurred. Commit/PR and exact-source CI remain pending.

Implementation/test fingerprint (docs excluded): `source_files=598`,

`source_sha256=88ec448032ecc102ab778e54e1f9b77b92728c14f3650328192e258f90da0b92`.

Population: Python under backend accord/tests/migrations; TS/TSX/CSS under frontend app,
TS under frontend lib; TS/TSX/MTS under frontend tests; plus `.env.example`, Next config and
the passport runtime grants. Hash sorted relative path, NUL, file bytes, NUL for each file.
This is an implementation snapshot, not a release or deployed-artifact identity.

Remaining gates, in order:
1. Source-bound complete checks and PR review/CI; disposable PostgreSQL migration, RLS,
   concurrent issuance/enrollment/publication replay and owner/foreign-role acceptance.
2. Permitted real evidence and portrait/reference corpus; settle reviewer evidence access and
   trusted retention/hold authority; run held-out recognition/calibration measurements.
3. Owner-authorized Linux/clamd/KMS/Redis/IAM/Google configuration, schema/grants and live probes.
   Before public activation: anonymous ingress rate/cost protection, event retention/capacity,
   trust-key lifetime/rotation, approved origin/CSRF and explicit publication consent.
4. Rendered creator/independent-reviewer/production/passport journey, phone QR scan,
   permission withdrawal/expiry, restart/replay and failure/isolation rehearsal (H5).
5. Licence/source inventory including QR notice, organizer publication/package terms,
   approved demo/pitch/video and submission (H6). No publication or submission occurred.

Future voice/video identity, web monitoring and shared/global search remain outside this prototype.
