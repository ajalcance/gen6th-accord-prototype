# Persona connection implementation — 2026-10-02

This source-bound checkpoint is followed by [read-side preparation](h2-read-side-review.md).
Its 397-test result remains evidence for this slice, not the subsequently changed tree.

Owner authorized this order: action/contract review, secure evidence handling, typed
frontend adapters, then journey tests. Owner visual feedback is preliminary; manual
interaction acceptance is deferred until the implementation is better connected.
The renewed session window still ends at 16:58:52 Asia/Manila on 2026-10-02.

## 1. Action and contract review

Source inspected: console reducer/types/use-studio, typed HTTP client, persona services,
models, migrations 0003–0006, and server route registration. All five screens remain
browser fixtures; no persona route is mounted. This table distinguishes behavior from
visual controls so presentation changes do not accidentally become authorization.

| Surface/action | Existing internal service | Connection requirement |
|---|---|---|
| Gallery create/open | `save` / `load` | Server UUIDs, workspace session, bounded authorized listing |
| Search/filter/grid/list | Browser presentation | Search only authorized records; never infer access from a card |
| Edit/save version | `SaveCommand`, immutable versions | Preserve draft, expected revision, stable request ID on retry |
| Evidence inspect/upload | Seeded `FixtureAsset` only | Separate private quarantine; byte validation, encryption, scan and expiry |
| Start/cancel/retry analysis | None; timer simulation | Future durable jobs and permitted model/data; keep simulation labelled |
| Compare/reference selector | SVG palette fixture | No matching, biometric or authenticity claim |
| Independent review/changes | `record_review`, review history | Trusted human reviewer, exact version/previous review, durable receipt |
| Offer scope | `offer_campaign` | Current approved version, exact fixture asset IDs, recipient and UTC scope |
| Accept/request changes/revoke | Campaign decision service | Trusted actor, previous decision CAS, explicit statement and request ID |
| Demo role/time selectors | No production equivalent | Never transmit these as trusted actor or current time |
| Eligibility | Campaign status service | Use server evaluation; acceptance alone is insufficient |
| Public/private preview | Browser allowlisted projection | Separate publication approval and privacy contract; no publish action |
| Unsigned export | Browser fixture JSON | Preserve unsigned/fixture status; signing is not connected |
| History/operations | Internal observations and retained audit references | Authorized reads; distinguish pending evidence from chain verification |
| Assistant/apply note | Scripted browser response | Human applies text; never auto-review, accept or grant permission |
| Navigation/drawers/sidebar | Local interaction | No backend mutation or security event asserted |

## Boundaries found

- Stored persona content and campaign assets explicitly require `fixture=true`. Real
  evidence must not be inserted into the fixture catalogue or silently relax that constraint.
- Version writes lack a user-facing authorized listing. Review/campaign services already
  enforce membership, independent actors, version binding, replay equality and conflicts.
- No trusted session adapter exists. Preparing transport contracts does not authorize
  mounting routes, accepting browser actor claims or substituting scaffold identity.
- Evidence bytes, malware scanning, private storage and encryption are absent. An accepted
  content type or digest alone cannot establish safe content. Scanner/key failures must deny
  promotion and reads; original filenames must not become paths or public URLs.
- The existing HTTP client overwrites caller cancellation and trusts generic response casts.
  Connection work must preserve cancellation and validate received shapes at runtime.
- There is no real analysis pipeline, public projection service or signing service. These
  remain separate gated roadmap work, not implied by this four-task authorization.

## Verification and review units

Keep contract review, evidence implementation and frontend transport separate from existing
dirty UI/backend/policy work. The pre-change backend fingerprint is
`7a50df9ccefa699e26d24ce4302729f332d95f3a1166666f4bba8906b4c1c082`
(120 inputs, owner checkpoint 349 tests). Any backend edit invalidates that checkpoint for
the changed tree. The frontend checkpoint is 85 tests; run fresh tests after adapter changes.
Full audit gates remain incomplete. Docker-backed validation is owner/CI-run.

## 2. Evidence implementation checkpoint

Implemented internal bounded encrypted quarantine (ADR-0031): metadata/inspection remain
immutable, encrypted payloads expire independently, reads require owner authorization and a
clean inspection, and purge requires an affirmative injected retention/hold decision.
Migration 0007 is prepared, not applied to the owner's persistent database.
Private evidence cannot be used as a fixture campaign asset.

The owner approved and installed `cryptography==50.0.2`, with `cffi==2.1.1` and `pycparser==3.0`
resolved by pip. Owner `pip check` and AES-GCM round trip passed; the agent independently
verified the installed version and ran real encryption fault tests. Sandbox installation
failed on registry DNS; no boundary was bypassed and no pip upgrade was requested.

**Incomplete activation:** no real bounded decoder/malware inspector, wrapping-key provider,
legal-hold/retention provider or automatic cleanup worker is configured. Clean inspection
remains temporary quarantine, not promoted restricted/sealed evidence. Only synthetic test
data was processed. Provider availability, quotas and promotion must be resolved before use.

## 3. Typed connection preparation checkpoint

ADR-0032 prepares save/load/review/offer/decision/status operations with runtime receipt and
tenant/version/scope validation. Mutation state preserves exact retry intent, handles pending,
conflict, denied, invalid, cancelled and uncertain outcomes without replacing an editable draft.
The shared HTTP client now preserves caller cancellation and supported header representations.
Default persona transport rejects; no route paths, session fallback or browser connection
were invented. Gallery listing/evidence/history transport remain follow-ups.

## 4. Validation checkpoint

| Check | Result |
|---|---|
| Frontend suite | 109 tests / 10 files pass |
| Frontend lint/format/types | Pass via `make frontend` before its audit failure |
| Frontend production build | Pass; separate build after the audit failure, not a full-gate claim |
| Backend targeted checks | 49 pass: encryption/input faults, shared wire contracts, migration rendering, spine registration and detection contracts |
| Backend database suite | Owner repeat passed all 397 tests in 62.05s; application coverage 96.35% (1,918 statements, 70 missed), existing 70% floor met |
| Full gate | 776 guards pass / 18 skip; policy/harness and backend lint/format/types/Bandit pass; pip-audit bootstrap fails |
| Frontend full gate | Stops at npm audit registry DNS (`ENOTFOUND registry.npmjs.org`) |
| Diff hygiene | `git diff --check` passes |

Current backend fingerprint:
`bec79bace7ab27ac36f3e5bc0105773039c070ca14bb6ee0ea6601eb3ca8089c` (136 inputs).
Current frontend fingerprint:
`b5692fbb04799698d53f34317e7f67a7fefa2bb8cf27d87d653a1a7a8a4efb7d` (70 inputs).
Both allowlisted fingerprint helpers now include the shared fictional JSON wire fixture.
The earlier 349-test owner result does not validate this changed backend tree.

Wire tests use a labelled injected test transport. The added internal PostgreSQL journey
tests creation, evidence isolation, independent review, campaign acceptance and revocation.
Neither proves authenticated browser-to-backend behavior; trusted sessions/API remain gated.
User manual acceptance remains deferred. No cloud, identity, signing or publication activated.

At the 18:00 Manila clock check, the 16:58:52 build cutoff had passed. Implementation stopped
for a window-renewal decision; the already-started production build finished successfully.
Owner renewed two hours: **18:02:25–20:02:25 Asia/Manila, 2026-10-02** for validation/fixes/handoff.
Source is preserved on the existing dirty branch; no commit, PR or deployment was made.

The owner database run supplied leading fingerprint
`c7cd95d8972e519feb26411cf3736582a0d71eefd0fcdc9e5666228a32054925` and stopped at
`test_detection_contract.py::test_write_rule_and_version_digest`: `len(PERSONA_ACTIONS)` is
13 after four evidence actions were registered, while the test expects 9. It passed 139 tests
before stopping in 34.56s. No trailing fingerprint or full coverage result was produced.
The agent independently rechecked that source fingerprint. Per AGENTS.md's explicit check-edit
rule, the owner approved replacing the stale count with an exact thirteen-action set while
retaining client exclusion. That correction and the targeted checks pass; the new fingerprint
above identifies the corrected tree. Owner repeat then passed **397 tests in 62.05s**, with
matching leading/trailing fingerprints. Agent independently rechecked the same fingerprint.
Application-only coverage is **96.35%**, with the existing 70% floor met. This verifies the
internal database workflow and migrations, not authenticated HTTP, provider activation or full audits.
Shared bundle verification passes at 166.4 kB gzip against 250 kB; `make dod-check` passes.

## Owner database validation

With Docker Desktop running, use Mac Terminal. The fingerprint precondition refuses a
different source tree; all tests use throwaway databases. No persistent database is migrated.

```bash
cd "/path/to/gen6th-accord" &&
test "$(backend/.venv/bin/python .cache/workflow-source-evidence.py)" = "backend_source_sha256=bec79bace7ab27ac36f3e5bc0105773039c070ca14bb6ee0ea6601eb3ca8089c files=136" &&
backend/.venv/bin/python .cache/workflow-source-evidence.py &&
LC_ALL=en_US.UTF-8 backend/.venv/bin/pytest backend/tests -q --cov=accord --cov-config=backend/pyproject.toml --maxfail=1 &&
backend/.venv/bin/python .cache/workflow-source-evidence.py
```

Expected: 397 passes, the existing coverage floor passing, and matching fingerprints.
If the block stops silently at the source precondition, refresh the checkpoint first.
