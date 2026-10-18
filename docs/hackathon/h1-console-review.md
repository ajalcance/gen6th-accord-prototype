# H1 console review — 2026-10-02

This is the preserved second/third-pass checkpoint. The owner-authorized
[fourth-pass review](h1-fourth-pass-review.md) supersedes its frontend scope and fingerprint:
85 tests/eight files pass; full audits and owner browser acceptance remain incomplete.

## Review units and boundaries

Owner approved second-pass operations and third-pass compact executive layout. Decisions:
[ADR-0028](../decisions/0028-persona-console-design-system.md) and
[ADR-0029](../decisions/0029-compact-persona-console.md). This unit owns `frontend/app/passport/`,
the page/global styles and frontend tests, plus their documentation hunks. Preserve the
preexisting setup/dependency, backend, publication and agent-policy units. Git metadata is
read-only to the agent; no branch, commit or PR was created. Owner review labels remain owner-only.

All inputs, personas, parties, evidence and results are fictional. No persona API or trusted
session is connected. No model, upload, encryption, signing, cloud, visibility/licence change
or deployment is activated. Hack2skill acknowledgment and eligibility/source-package questions
remain pending in [publication record](publication-record.md); [RIGHTS.md](../../RIGHTS.md) applies.

## Implemented local experience

| Module | Behavior and truthful boundary |
|---|---|
| Shell | Collapsible sidebar, consistent task titles, keyboard commands, scrollable workspace and anchored status footer |
| Gallery | Search/filter, independent records and one-to-five container-responsive columns; minimal text/icon actions, no invented extra fixtures |
| Creation | Four bounded fields including AI disclosure, draft-only autosave, completeness and smaller live reference preview |
| Analysis | Five deterministic stages, cancellable/retryable simulation, palette/control references and actual two-SVG comparison |
| Review | Independent fictional actor, self-review denial, explicit note application and exact-version decision invalidation |
| Campaign | Creator offers, named recipient acceptance/change request, final revocation, bounded scope and separately recomputed fixture eligibility |
| Public preview | Committed-field projection, private-note exclusion, explicit unsigned verification and allowlisted JSON export |
| Drawers | Source-linked scripted assistant, bounded tab-local history, filtered commands and internal backend readiness |
| Security status | Static local interface presence; trusted identity/monitoring disconnected and signatures unavailable; no breach verdict |

Only `id`, palette variant, bounded draft fields and selected index are persisted (schema 2).
Malformed/oversized storage fails closed; legacy drafts receive a declared fictional disclosure.
Restoration drops forged approvals, roles, notes, analysis and history. At most 12 records and
50 history entries per record. Version/history entries are simulations, not server receipts.
Changing artifact content cancels/reset analysis and clears decisions/old notes. Campaign
changes preserve independent persona review but withdraw acceptance. Scoped dates are UTC
calendar dates with positive duration at most 366 days. The clock selector is explicitly simulated.

## Design acceptance

- Density tokens: 24–28px page titles, 18px section headings, 14px working text and 12px metadata;
  36px desktop controls, 48px header, 36px desktop footer, 20px panel padding and 6–8px radii.
- Touch controls remain at least 44px tall. Footer stays outside the workspace scroller and
  includes safe-area padding. Focus outline fits its compact control.
- Gallery uses workspace container widths 480/720/940/1140px for two/three/four/five columns.
  Collapse can recover enough space for another column. Only three seeded records exist.
- Cards retain minimal status badges and omit repeated studio labels/oversized controls.
  Pending review and passport context share a two-column support row from 720px.
  Open record is text
  plus icon, revealed on desktop hover/focus and visible on touch. The whole card is operable.
- Required decisions/blockers remain visible; demo-only interruption controls use native details.
  Biography/contribution share two columns; name/disclosure span the form, with mobile stacking.
  Static presence does not pulse. Scan/drawer transitions honor reduced-motion preferences.

## Validation checkpoint

Current frontend: 73 tests across seven files pass, zero-warning ESLint and strict TypeScript
pass. Tests include whole journey/no fetch, independent drafts/restoration, actor/expiry gates,
scope/date validation, cancellation/stale completion, bounded history, public export allowlist,
modal focus/escape/trapping, command search and anchored-footer DOM structure.
The final production build passes. Shared client JS is 166.4 KiB gzip against the unchanged
250 KiB gate. Supplemental page-reference measurement is 186.9 KiB gzip across ten unique
JS files, including 20.9 KiB route-specific JS; this is not a field-performance/Lighthouse score.
Source fingerprint: `9706f25708042a10859d3473a9ec56b3c4df0c6a1a3115628cd7576c23cc429f`
across 54 frontend inputs (independently rechecked after the final code/test changes).

Fresh `make check` with Python 3.12/Node 22 passed preflight, 776 guards (18 skipped), policy,
harness and backend Ruff/Black/Mypy/Bandit, then stopped at pip-audit temporary-environment
bootstrap (`Failed to upgrade pip`). No backend database tests or subsequent gates ran.
`make frontend` passed lint/format/types then npm audit failed because registry.npmjs.org
DNS was unavailable. Separate tests/build/budget above passed; they do not bypass the audits.
`make dod-check` passes. Initial use of the system Python 3.9 stopped on missing tomllib/zip
strict support; selecting the installed backend Python 3.12 corrected the toolchain, not a guard.
Passport TS/TSX functions are within 50 lines and files within the 400-line hard cap. PLAN's
older foundation progress was moved intact to [history](../plan-foundation-history.md), retaining
the full Stage 0–9 checklist in PLAN. Existing setup/backend/policy changes remain preserved.

Backend source remains the owner-validated 120-file fingerprint:
`7a50df9ccefa699e26d24ce4302729f332d95f3a1166666f4bba8906b4c1c082`.
All 349 backend tests previously passed in 63.41s; application-only coverage re-report was 96%.
No backend change belongs to this UI unit. Full repository gates are not yet green.

## Owner visual review

The source dev server is already listening on loopback 18664. Refresh
[local preview](http://127.0.0.1:18664). Port 18660 is the separate Docker image and can show
older UI until owner rebuild. Preview opening was queued in Codex; browser automation exits
before a usable session, so no agent claim of browser geometry/accessibility certification.

Review all five screens at desktop, laptop, tablet and 320/390px mobile widths, including:

1. Sidebar expanded/collapsed; every destination remains discoverable, with no clipped focus.
2. Gallery five-column wide layout, narrower reflow, empty search, touch and keyboard card actions.
3. Footer/header height, readable status, no content overlap, short viewport and 200%/400% zoom.
4. Creation fields/preview, scan cancel/retry/comparison, review blockers and campaign parties.
5. Drawer focus/escape/return, background inertness, scrolling and reduced-motion setting.
6. Public/private presentation and unsigned export; private notes never enter public JSON.

DOM tests and bundle weight do not establish impeccable spacing, field performance or WCAG
conformance. Capture remaining visual defects before expanding scope or claiming commercialization.

## Repeat frontend checks

Run in the owner's Mac Terminal; dependencies are already installed. No services are activated.

```bash
cd "/path/to/gen6th-accord"
(
  set -euo pipefail
  export PATH="/opt/homebrew/opt/node@22/bin:$PWD/.tools/bin:$PATH"
  backend/.venv/bin/python .cache/frontend-source-evidence.py
  cd frontend
  npm run lint
  ./node_modules/.bin/prettier --check .
  ./node_modules/.bin/tsc --noEmit
  npm audit --audit-level=high
  npm test
  npm run build
  npm run bundle-size
  cd ..
  backend/.venv/bin/python .cache/frontend-source-evidence.py
)
```

Share the test/build/audit summaries and matching before/after frontend fingerprints. The
scratch fingerprint helper is local/ignored; it is not a CI gate. Full `make check` and
revision-bound PR/CI evidence remain required separately. Do not widen permissions or alter
guards to complete an unavailable check.
