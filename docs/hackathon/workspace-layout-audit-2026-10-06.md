# Workspace layout audit — October 6, 2026

The owner reported successful sign-in after restoring the existing process override, then showed
the performer picker and selected Analysis workspace. The screenshots exposed form-margin
inheritance, repeated context headings, oversized feedback, tightly adjacent controls and duplicate
review-request history. The owner explicitly requested a cross-page audit and fixes.

This pass inspects page composition, shared styles and source/DOM state transitions. Browser driving
remains prohibited by the project runbook. It does not claim a rendered desktop/mobile/zoom audit.
The owner's screenshots are rendered evidence for the reported cases; the updated layout still
needs owner visual review. ADR-0059 remains the design decision; no new server action is introduced.

## Audited surfaces and corrections

| Surface | Review and resulting treatment |
| --- | --- |
| Shell, navigation, Help/Actions | Retain semantic navigation, existing narrow-screen wrapping and modal focus handling. Remove the redundant performer-workspace eyebrow above journey page titles. Preserve Settings and capability access. |
| Records | Retain toolbar name/image entry points, grid/list, bounded paging and return-state behavior. Shared read feedback becomes a compact message/action row; failed reads never become an empty result. |
| System Capture | Retain the single field labels/placeholders, progressive declarations, portrait Scan, explicit first-reference approval and local helper. No new persistent panel or implicit processing added. |
| Performer selection | Dedicated 640-pixel panel with an accessible placeholder search, aligned 44-pixel controls, page-local count and full-row Select action. Name and saved version stay distinct. Search stacks in narrow workspaces; long names wrap. No thumbnail/provider request is added. |
| Saved profile/References | Retain section navigation and loaded version. Capture-profile feedback names the affected resource. Technical values and package text wrap without expanding the workspace. |
| Analysis | A contained workflow panel, one Investigations heading and a quiet contextual Records action replace stacked repeated page/version headings. Review-request history is not mounted or fetched in this tab. |
| Independent review | Decision, decision history and saved request history remain distinct. Requests live here, with the same exact-version binding, denial propagation and retries. Refresh moves into the section heading. Failed reads retain visible scoped alerts. |
| Production & use | Shared workflow spacing, checkbox alignment and full-row explanatory paragraphs/offer summary fix nested form layout. Production offer and review headings avoid repeating the version already shown in workspace context. Metadata selection and explicit confirmations stay intact. |
| Passports | Production scope receives a contained panel. Keep private issuance, public sharing and verification separate. Warnings identify the configuration needed by the selected action; missing verification keys do not imply missing signing in the private-issuance tab. Public field preview and approval/withdrawal boundaries remain. |
| Evidence & assets/Activity | Shared form/control spacing, wrapping and scoped history feedback apply. Existing explicit upload/inspect/download/enroll and historical-version controls remain. No automatic evidence read or action is added. |
| Settings | Capability sections get consistent spacing and surfaces; processing flags use labelled columns that stack at narrow widths. Copy distinguishes session configuration from each capability's acceptance. Local report validation and tab-only preferences are retained. |
| Public passport | Bound the reading width, style native action controls, wrap disclosures/package text and stack field columns at narrow widths. Public routes remain disabled unless separately activated. No serving/publication occurs in this audit. |

Shared `ReadFeedback` preserves each error category and retry/stop action. Named resources replace
the generic Records message where appropriate. Denied/invalid/expired states do not acquire a retry.
History/discovery pagination is omitted only when the first page has no next cursor; paging remains
available when a server cursor or previous-page position exists. No global total is invented.

## Operational distinction

The screenshot's unavailable investigation/request messages represent real unsuccessful reads.
This layout work does not establish their backend cause or restore providers, SQL grants or schema.
Only a successful read can show findings or an empty history. Scope-specific feedback points to
capability status in Settings; it never converts unavailable data into success.

No package installation, service restart, private configuration read/change, migration/grant,
key/provider activation, cloud/model call, public publication or checkout cleanup occurred.
The production build uses an isolated source copy under `.cache/frontend-layout-build-2026-10-06`
and the existing node_modules; it does not write to the running preview's `.next` directory.

## Verification checkpoint

### October 7 entry refinement

The owner supplied screenshots of all three unselected destinations and approved the proposed
refinement. They intentionally share authorized performer selection, but now explain distinct
tasks: compare/review appearances, manage production offers/permissions, and issue/share/verify
passports. Selection rows say Open analysis, Manage production use or Open passports, including
performer/version in their accessible names. Capability availability remains governed by the
selected workspace's existing configuration and access checks.

The exposed label came from a hidden-label utility scoped only to System Capture; that existing
utility now lives in global CSS. The narrow search inherited the Records toolbar width; a scoped
picker rule now fills its grid track next to Find performer. The compact panel keeps 44-pixel
search controls and bounded page-local results; narrow layouts stack the form and put the
workflow action beneath the name/version. Selection remains deliberate even for one result.
The existing compact performer/version header and Change performer remain on selected workflows.

This implements ADR-0059 rather than introducing a new decision. New source/DOM cases check each
destination's guidance/action, distinct workspace entry, bounded submitted search and performer/
version continuity through navigation and explicit selection clearing. Rendered width/zoom/touch
review remains pending. All 502 frontend cases across 90 files pass (including five new picker
cases); the report is `.cache/performer-entry-tests-2026-10-07.json`. Scoped ESLint/Prettier,
full TypeScript and the isolated production build pass. Compiled CSS includes the global hidden
label rule and picker width override; this is not browser geometry evidence. Shared client bundle
remains 167.0 kB gzip against the unchanged 250 kB budget. DoD and diff-whitespace checks pass.
The isolated build lives in `.cache/frontend-entry-build-2026-10-07`; the live `.next` is untouched.
The npm audit retry still fails with `ENOTFOUND registry.npmjs.org`; full-green status stays open.
`make check` passes 776 guard cases (18 skipped), policy, harness and backend static checks,
then stops at pip-audit's temporary pip-bootstrap failure. Backend database tests and subsequent
aggregate targets are not reached by that run; the frontend results above use separate runners.
Existing checkout changes, branch and HEAD are preserved; no runtime activation or service restart.

### October 6 snapshot

All 484 frontend tests and 17 isolated ASGI-to-UI integration tests pass, including scoped
unavailable-history recovery, exact-version retries and review-request loading only in Independent
review. Results are retained locally in `.cache/layout-audit-tests.json` and
`.cache/layout-audit-integration.json`. These integrations use synthetic providers/sessions.
ESLint, Prettier, TypeScript and the isolated production build pass. Shared client bundle is
167.0 kB gzip against the unchanged 250 kB budget. Policy, DoD and diff-whitespace checks pass. Scoped gitleaks reports no
leaks; Semgrep runs two applicable rules across 97 TypeScript targets with zero findings.

Branch remains `security/codex-agent-boundary`; HEAD remains
`407a9f4a67611770143198d1f42d605738b01530`. Existing tracked/untracked work is preserved.
Current source snapshot: `source_files=630`,
`source_sha256=ea6a82508fbc0ca70903247dde2a4db9c51d61c10e34d4b558b4cd0c472cb446`.
Use the allowlisted population and path/NUL/bytes/NUL algorithm in
`next-session-2026-10-06.md`; docs/cache/private config are excluded. The handoff's 607-file and
initial redesign's 627-file fingerprints are historical, not values to restore.

The earlier full gate stopped at pip-audit's temporary pip upgrade failure; npm audit reported
`ENOTFOUND registry.npmjs.org`. Neither required audit is bypassed or marked passed here.
This layout pass uses the relevant frontend/integration runners; it does not rerun or close the
full gate, database-backed backend suite or live provider acceptance.
Owner review should cover all destinations, selected/unselected contexts, keyboard focus, long
values, 200% zoom, narrow layouts, failed reads, retry recovery and actual authorized journeys.
Dependency audit/full-green, SQL/provider and recognition/runtime acceptance remain separate.
