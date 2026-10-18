# Performer workspace redesign — October 6, 2026

Later owner screenshots prompted the [current layout audit](workspace-layout-audit-2026-10-06.md).
The validation/fingerprint below describes the earlier redesign checkpoint; use the audit record
for the latest source and review state.

The owner approved the comprehensive UI direction after reviewing Records/System Capture,
then requested an on-demand helper in place of the wide capture progress panel. ADR-0059
records the decisions. This work changes frontend source and tests in the existing dirty checkout.
Existing backend, configuration, schema, guards and unrelated changes are preserved.

## Implemented experience

| Surface | Behavior |
| --- | --- |
| Records | Name search and expandable image search share the toolbar. Identical file and Similar face are distinct modes. Grid/list, submitted query and bounded cursor history survive record inspection. Paging appears above/below results. |
| System Capture | Name initially expanded; other required declarations collapsed with status and counters. Each field has one visible label and an instructional placeholder. Portrait guidance appears once. Capture helper beside Register persona tracks missing details, scan and confirmation; selecting a step opens/focuses its control. Explicit confirmation approves the portrait as the first reference. Longer guidance appears on demand. |
| Saved performer | Overview, References, Evidence & assets and Activity organize existing capabilities. Direct edit, loaded-version context, explicit version history/current reload and copyable storage/provenance references. Historical Activity has its own labelled version selector. |
| Analysis & review | Selected performer/version follows navigation. Otherwise an authorized searchable picker appears. Analysis findings and independent human review have separate sections and access limits. |
| Production & use | Current permission, Create offer and Recipient decision reuse existing authorization. Optional supporting consent/ownership references come from scoped metadata, up to eight. A scope summary precedes confirmation. |
| Passports | Separate Private issuance, Public sharing and Verify package sections. Public field selection has a recipient preview. Existing approval history, withdrawal, signature verification and current permission remain separate. |
| Shell/Settings | Settings and Help in sidebar utilities; account actions in header. Connection & capabilities, Recognition evidence and tab-only presentation preferences in Settings. Footer opens Settings. |

Text declarations are authored claims. Automatic capture metadata is limited to actual returned
dimensions, orientation, processing recipe/version, digests and timestamps. Saved reference/face
screens retain detected boxes, quality/selection state, representations and readiness. No biography,
rights, identity assurance, extraction result or cryptographic secret is invented from a portrait.
Recognition processing remains a post-registration explicit action against saved approved references.
Other authoring forms use placeholders for short entry guidance while retaining persistent field
labels, validation errors, permission statements and consequential approval text. The capture
footer keeps Register persona, the helper and a quiet Back to records action; connection/access
problems remain visible. The helper guides completion without repeating a permanent status panel.

No global status queue, global total, fabricated confidence, timeline aggregation or persistent
preference API was added. Those require separate contracts. The helper is deterministic local UI;
it never scans, saves, fills declarations or invokes a model on the user's behalf.

## Validation and boundaries

Validation is source/DOM and isolated synthetic integration evidence, not rendered acceptance.
The full repository gate passes preflight, 776 guard tests (18 skipped), policy/harness,
Ruff/Black, mypy over 337 files and Bandit, then stops at pip-audit's existing pip bootstrap failure.
The separate npm audit also fails at registry DNS. Neither audit is reported green or bypassed.
Final frontend evidence and the current working-tree fingerprint are recorded below.

No packages were installed by this task, services restarted, migrations/grants run, keys activated,
cloud/model calls made, publications prepared or checkout changes cleaned. Existing user actions
in the running preview are not claimed as agent acceptance. Browser automation remains outside
the project permission boundary. Owner review should cover desktop/narrow layouts, 200% zoom,
keyboard/focus, touch targets, long records, helper placement and real authorized journeys.

Actual permitted recognition measurement, Google/runtime acceptance, current SQL authorization,
live independent-review rehearsal and publication/submission remain pending. The earlier
`next-session-2026-10-06.md` fingerprint is historical; do not use it for this redesigned source.

## Final source checkpoint

- 483/483 frontend tests and 17/17 isolated HTTP-to-UI ASGI integrations pass. They use
  synthetic sessions/providers and do not certify SQL/RLS, real recognition or rendered layout.
- ESLint (zero warnings), Prettier, TypeScript and production build pass. Shared client bundle:
  166.4 kB gzip against the unchanged 250 kB budget.
- `make policy` and `make dod-check` pass after the final changes. Required dependency audits
  remain unresolved as described above; there is no full-green or release-readiness claim.
- Scoped passport UI checks: Semgrep runs two applicable TypeScript rules on 97 files with
  zero findings; redacted gitleaks directory scan finds no leaks. These are bounded source scans.
- Branch: `security/codex-agent-boundary`; HEAD: `407a9f4a67611770143198d1f42d605738b01530`.
  The checkout remains dirty with the earlier prototype work preserved. No commit or PR created.
- The final port check finds no listener at `127.0.0.1:18664`. No service was started or restarted.

Working-tree source fingerprint, including untracked source/tests and excluding docs:
`source_files=627`
`source_sha256=2f29155c413f0a48493e62e350c0ae870f1663a3a3ecf884c34e3227bcc19034`

Population and hashing follow the earlier handoff: Python under backend accord/tests/migrations;
TypeScript/TSX/CSS under frontend app, TypeScript under frontend lib, TypeScript/TSX/MTS under
frontend tests; `.env.example`, `frontend/next.config.ts`,
`deploy/accord-passport-runtime-grants.sql`. Hash sorted relative POSIX path bytes, NUL, file bytes,
NUL for each file. This binds current source, not a deployed artifact or repository HEAD alone.

The next checkpoint is owner frontend review, with particular attention to search discovery,
keyboard navigation through collapsed required fields, helper focus/placement, registration
confirmation, version context, evidence selection and the public-recipient preview. No further
roadmap slice or runtime activation is authorized by completion of this UI work.
