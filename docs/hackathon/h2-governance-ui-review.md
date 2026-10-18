# Visible governance and draft recovery — 2026-10-03

The owner explicitly authorized exposing prepared backend concepts and finishing empty,
unavailable, permission-loss and version-conflict interactions. Work remains inside the approved
**06:57:39–08:57:39 Asia/Manila, 2026-10-03** window. No automatic extension.
Decision: [ADR-0035](../decisions/0035-visible-governance-and-draft-recovery.md).

## Working local result

From any of the five screens, open **Evidence & decisions** in the sidebar. On mobile, open
**Quick actions**, search **Evidence**, then select **Evidence & decisions**. Refresh the source
[preview on 18664](http://127.0.0.1:18664/) if the entry is missing. Port 18660 is an older Docker
image. The 18664 loopback listener was rechecked (Node PID 51509); Codex's browser open request
was queued. Agent HTTP could not connect from its sandbox; no rendered browser acceptance is claimed.

The panel has five sections:

- **Versions:** immutable version snapshots and human/AI disclosures, unsigned reference metadata.
- **Reviews:** distinct fictional reviewer, exact-version approval/change history, bounded paging
  and audit reference inspection. Version 3 has no review; version 2's approval cannot approve it.
- **Campaign:** scope, recipient, assets/time window, revocation and historical acceptance.
  Current blocked use remains separate from the decision history.
- **Evidence:** quarantined, inspection-passed, rejected and expired metadata. Inspection does not
  promote private evidence; expiry blocks access without claiming deletion. The whole view clears
  if an item fails validation or loses permission, with one useful recovery message.
- **Save recovery:** conflict comparison against a separate fictional latest version, permission
  prerequisite, uncertain/cancelled outcomes and explicit same-request retry. No real save occurs.

**All examples are fictional, use a frozen clock and make no network requests.** Their record
is separate from editable browser personas and saved server data. No actor selector, example
reset, audit reference or inspection result establishes identity, permission, rights or signing.
Normal read transport rejects writes; the separate save simulation returns a typed example
receipt without changing records, local versions, localStorage, approvals or visibility.

“Preview conditions” exposes populated/empty/unavailable/denied read examples. Empty states
offer actual Creation/connection navigation. Transient reads offer explicit retry; denied reads
clear data and do not retry. Restoring an example changes only fixtures. Close/Escape preserves
drafts. The panel uses compact typography/actions, a sticky header, native disclosures, keyboard
focus containment/return, stable paging controls and responsive two-column sections. Mobile/coarse
pointer targets and reduced-motion rules inherit the existing design system.

## Current validation and provenance

- **192 frontend tests / 17 files pass**, including 41 new governance/recovery cases.
  Tests exercise all sections, five-screen and command access, focus return/paging, version
  binding, audit actor/event/exact-time binding (including fractional mismatch), empty/denied/
  unavailable states, conflict comparison,
  draft/version preservation, uncertain/cancelled retry, late-result isolation and no HTTP writes.
- ESLint, full Prettier check, strict TypeScript, production webpack build and bundle budget pass.
  Shared client bundle remains **166.4 kB gzip / 250 kB**.
- **19 actual current example payloads** validate against unchanged backend Pydantic models
  (versions/reviews/campaign/decisions/status/evidence/audit), without database access.
  This is contract proof, not an authenticated browser/backend journey.
- Backend source is unchanged at **146 inputs**:
  `84eb16651371c1b5f54e3cf75b0e27e007ec35cca9f8b48303fe155df7d5698f`.
  Its owner **454-test / 96.55% coverage** checkpoint still applies; no redundant SQL rerun
  is requested for this frontend-only slice. The shared wire JSON was preserved.
- Frontend source: **101 inputs**:
  `7176266f1271f0a406bd014205c167b0d567f5f44e2867bc73546facf1b3fa31`.
- Agent `make frontend` passes lint/format/types then stops at npm audit registry DNS
  (`ENOTFOUND registry.npmjs.org`). No dependency manifest/lockfile changed in this slice,
  but the current complete frontend gate is not claimed green. The previous owner full gate
  remains historical in the [session/read checkpoint](h2-session-read-review.md).
- File/function bounds, documentation consistency and diff hygiene are checked separately.
  Rendered mobile/zoom/touch/reduced-motion acceptance and revision-bound CI remain pending.

## Owner frontend gate

No terminal command is needed to inspect the UI. For the current audit gate, use **Mac Terminal**
with the installed Node 22/Python environment. No Docker, package installation, persona API,
database migration or cloud activation is required. Both preconditions stop on source drift.
Report the gate result and both final fingerprint lines; keep the current source stable while it runs.

```bash
cd "/path/to/gen6th-accord" &&
test "$(backend/.venv/bin/python .cache/workflow-source-evidence.py)" = "backend_source_sha256=84eb16651371c1b5f54e3cf75b0e27e007ec35cca9f8b48303fe155df7d5698f files=146" &&
test "$(backend/.venv/bin/python .cache/frontend-source-evidence.py)" = "frontend_source_sha256=7176266f1271f0a406bd014205c167b0d567f5f44e2867bc73546facf1b3fa31 files=101" &&
backend/.venv/bin/python .cache/frontend-source-evidence.py &&
PATH="$PWD/backend/.venv/bin:$PWD/.tools/bin:/opt/homebrew/opt/node@22/bin:$PATH" make frontend &&
backend/.venv/bin/python .cache/workflow-source-evidence.py &&
backend/.venv/bin/python .cache/frontend-source-evidence.py
```

## Review units and next gates

Preserve prior uncommitted work. Review governance reads/fixtures, save recovery and their
documentation/ADR as distinct units from the existing backend evidence, session preparation,
policy and dependency work. No staging, commits, branch switch, PR, labels or deployment occurred.
Owner-applied ADR/security review labels and revision-bound full CI are still required before merge.

Show this local result for feedback before expanding scope. The owner has deferred manual
acceptance until a better connected setup exists. Connection still requires approved Zynth
inspection/activation, trusted identity mapping/revocation, reviewed credentials/origin/CSRF/
TLS/headers and actual routes. Evidence intake still needs real key/scanner/retention providers.
No live monitoring, model analysis, signing, publication, visibility/licensing change, cloud or
deployment is authorized. Hack2skill clarification remains pending. Keep the full Stage 0–9 roadmap.
