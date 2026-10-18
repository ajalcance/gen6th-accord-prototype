# H2 PR/security readiness — 2026-10-03

Owner authorized next-task review, then renewed **21:07:44–23:07:44 Asia/Manila, October 3**
for record corrections and separate PR/provider-scope preparation. No new activation scope.

## Result and evidence

Reviewed verifier/write boundary, transactional authorization/replay, prepared transport,
authored-intent recovery and session/resource remounting. No new runtime defect was confirmed
in those paths. ADR-0037 and the write/security/handoff records now distinguish successful
owner local validation from historical SQL/audit failures and pending PR/CI/rendered acceptance.
No source, migration, dependency, scanner, gate or policy change is included in this review.

All three implementation fingerprints independently match the
[owner validation checkpoint](braces-installation-proposal.md). Preserve its full local gate
and 14 ASGI tests as owner-reported proof; the supplied tail omits preceding detailed output.
These unchanged implementation inputs do not need another owner SQL run for this records-only unit.

Supplemental SAST completed with **exit 0**, **11 applicable dangerous-operations rules /
211 Python and TypeScript targets / zero findings**, approximately **99.9% parsed lines**.
The targets include untracked persona source/tests, detection modules, passport source,
frontend libraries/tests and the docs-site braces regression. Sixteen configured rules remain
unchanged; Go rules have no targets in this slice. This is neither all-language/full-security
certification nor the community-rules CI scan.

The first tool attempts failed at CA setup and home-directory logging. The successful run
uses the installed certifi CA bundle and project-local log/settings files within the sandbox.
No certificate verification or findings check was disabled. Reproduce this scoped scan using
the existing installed tool, from the repository root:

```bash
SSL_CERT_FILE=backend/.venv/lib/python3.12/site-packages/certifi/cacert.pem SEMGREP_LOG_FILE=.cache/semgrep-readiness.log SEMGREP_SETTINGS_FILE=.cache/semgrep-readiness-settings.yml semgrep scan --config .semgrep/dangerous-ops.yml --error --metrics=off --no-git-ignore backend/accord/personas backend/accord/command/detection.py backend/accord/command/detection_events.py backend/accord/command/detection_models.py backend/tests/personas frontend/app/passport frontend/lib frontend/tests docs-site/tests/braces-depth.test.ts
```

## Live GitHub findings

Repository metadata and a live `AGENTS.md` fetch verified read connector access.
The observed [PR #50](https://github.com/ajalcance/gen6th-accord/pull/50),
`security(codex): add managed agent boundary`, is open at
`407a9f4a67611770143198d1f42d605738b01530`, matching local HEAD on
`security/codex-agent-boundary`. Its 15-file policy diff does not contain the current dirty
persona/dependency implementation. Combined legacy status entries are empty; the PR-run
endpoint returns completed run **36528663199**, conclusion **startup_failure**.
That endpoint lists only PR-triggered runs on its first page. No green CI proof was found
through the inspected endpoints; this is not a claim about every historical workflow.
Resolve the startup failure through the owner/GitHub before relying on CI.

GitHub capabilities are not owner authorization to label, approve or merge. No PR is created,
updated or attached by this preparation; #50 is background context for the checkout.

## Separate review units

The existing branch mixes earlier dependencies, local runtime, policy and H1/H2 work.
Whole-file staging of the npm manifests/locks would combine Next/Vitest changes with braces;
frontend's manifest also contains the two-runtime integration script. Resolve the selected
base and use matching hunks. The locked Next/Vitest baseline must agree with the tests;
an unrelated dependency PR is not automatically the appropriate base.

| Unit | Files/hunks to review | Dependency or gate |
| --- | --- | --- |
| Existing policy/local runtime | Existing policy PR and local-delivery files/tests/ADRs | Keep outside persona/dependency units; owner policy review |
| Dependency baseline | Previously approved Next/Vitest manifest/lock hunks | Reconcile before extracting the private backport; do not regenerate unrelated versions |
| Private braces correction | `vendor/braces/`; both app archive copies; both `braces-depth.test.ts`; braces-only manifest/lock hunks; frontend Docker archive COPY; ADR-0038; matching docs | Both build contexts and canonical source must be included; owner maintenance review and unchanged audit |
| Persona persistence/workflows | Contracts/models/repositories/services/policies; migrations 0003–0005; matching persistence/review/campaign tests and ADRs 0024–0026 | Foundation for later units; owner migration review |
| Durable observations | Detection modules and spine registration/control/audit changes; migration 0006; matching tests and ADR-0027 | Preserve client/server exclusion; owner sensitive audit review |
| Private evidence | `evidence_*` source; migration 0007; private-evidence tests; ADR-0031 | Unmounted quarantine; real providers absent; owner migration review |
| H1 browser journey | `frontend/app/passport/` fixture shell/screens/state/styles; page/style hunks; matching console tests and ADRs 0023/0028–0030 | Fictional/unsigned; rendered acceptance pending |
| Connection/read/governance | Typed commands/receipts/query/gateway/read libraries; gallery/history/session/governance source; saved/governance UI/tests; ADRs 0032–0036 | Depends on foundation and H1; verifier/source remain unavailable by default |
| Prepared writes/recovery | `write_http.py`; write/session tests; prepared-write transport/mutation and fixture forms/tests; ASGI helpers/config/script hunk; ADR-0037 | Depends on preceding uncommitted units; owner local ASGI proof is separate from CI |
| Current record correction | ADR-0037 status, PLAN/LESSONS/as-built/SECURITY/CHANGELOG and handoff/review documents | Metadata gate still requires owner ADR review; no decision or checker logic changes |

These are reviewer boundaries, not a claim that each row applies independently to current
`main`. Shared initialization, observation and documentation hunks must follow their actual
imports/registrations. The write slice cannot be published alone with its foundation missing.
Preserve the already approved write-role-loss fixture correction; do not request it again.

## Paste-ready PR description drafts

Use these only after the owner-reviewed extraction produces the stated diff. Add the actual
submitted revision and its CI result then; local whole-tree proof cannot certify a changed base.

### `security(deps): bound braces depth with an integrity-pinned private backport`

The Next lint dependency chain in both npm apps reaches the affected braces 3.0.3 parser.
Adopt the owner-reviewed private depth correction, preserving published parser behavior and
the original MIT license. Both apps pin the identical local archive through a direct development
dependency and scoped micromatch override; frontend Docker copies the archive before frozen
installation. Canonical source, patch and provenance remain available for review.

Validation: owner complete local gate and 14 ASGI tests pass on the recorded combined inputs;
agent verifies archive/source/lock identity, both installed consumer chains and 20 regressions
per app. Prior isolated released-case/consumer evidence is linked in the dependency checkpoint.
Submitted-revision CI remains required. Owner accepts temporary maintenance and source-lineage
advisory review; no audit exemption or forced lint downgrade is applied.

### `security(personas): prepare verified fixture writes with exact-intent recovery`

Prepare four unmounted version/review/campaign write operations using the required session
verifier and existing transactional services. Structured saved-record fixture forms require
explicit confirmation. An uncertain write retains its request ID/content across cancellation,
navigation and denied retry; conflicts preserve authored text and require new comparison and
confirmation. Lost access clears fetched records while retaining only authored studio memory.

Validation: current write checkpoint records 127 isolated backend boundary cases, 233 standard
frontend tests and 14 additional synthetic ASGI-to-UI cases. Owner PostgreSQL/Trust proof and
complete local gate pass. Submitted-revision CI, owner security/ADR review and rendered acceptance
remain open. No real identity provider, persona route, upload, model, signing or deployment is activated.

## Owner browser acceptance

Current-source listener was Node PID 51509 on loopback **18664**. CUA still fails at sandbox
initialization (`TIOCSTI`), and agent curl cannot connect. Browser-panel opening was queued,
not verified loaded. No out-of-sandbox retry or current rendered certification is claimed.
Port 18660 is the separate older Docker image. Verify current listener before reuse.

No terminal command is needed if [the source preview](http://127.0.0.1:18664/) opens on the Mac:

1. Open **Evidence & decisions**, then **Versions**, **Reviews**, **Campaign**, **Evidence**
   and **Save recovery**. Expand **Preview conditions**; try **Empty workspace**,
   **Unavailable service**, **Permission lost**, then **Restore populated example**.
2. In **Save recovery**, try conflict/unavailable/permission-loss examples and **Keep draft & close**.
   Confirm the authored browser draft remains intact.
3. Return to the gallery and choose **Saved records**. Default connection must show
   **Saved records are not connected**. Keep test verifier/gateway injection under tests.
4. Review all five screens/drawers at desktop/tablet/390px/320px, 200%/400% zoom and short height.
   Check sidebar states, grid/list reflow, wrapping and unobscured header/footer/content.
5. Check Tab/Shift+Tab, Enter/Space, Escape/focus return, disclosures, comparison slider,
   touch and reduced motion. Report pass/fail with screen/control and viewport.

This can certify only the labelled browser journey. Authenticated saved/write acceptance
requires a separately approved secure connection; synthetic tests are not that acceptance.

## Next scope

The [evidence-provider preparation plan](evidence-provider-integration-plan.md) maps the
existing interfaces, missing provider evidence, decisions and fault tests. It proposes the
next implementation unit; no provider is selected, installed, configured or activated.
Zynth, credentials, public visibility/licensing, cloud, models, signing and deployment remain gated.

## Record-only verification

Fresh `make check` passes **776 guards / 18 skips**, policy/documentation checks, harness,
backend Ruff/Black/mypy (146 source files) and Bandit. It then stops at pip-audit bootstrap:
**Failed to upgrade pip**, exit 2. SQL, Trust and app gates are not reached by this agent run.
No checker, install scope or sandbox is changed to make it pass. Relevant document gates pass;
the earlier complete owner run remains evidence for unchanged implementation inputs.

All three implementation fingerprints match before/after these records-only changes.
Diff hygiene passes; changed documents meet the 400-line cap (PLAN 398, as-built 400).
No new behavior test is added for the documentation correction. Revision-bound CI is still open.
