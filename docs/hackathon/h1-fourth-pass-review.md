# H1 fourth-pass console review — 2026-10-02

Owner authorized all five screens and shared UI refinements after an element-level source
review. [ADR-0030](../decisions/0030-task-focused-persona-console.md) records the decision.
The renewed work window is 11:58:52–16:58:52 Asia/Manila on 2026-10-02.

## Review unit and boundaries

This unit changes only frontend source/tests and associated records. Prior dirty setup,
dependency, backend, policy and planning units remain preserved. No branch/commit/PR or
owner review label is created; git metadata remains read-only. Select matching documentation
hunks when preparing separate owner-reviewed PRs.

All personas, inputs, events and decisions remain fictional/browser-only. No persona API,
model, identity, uploads, monitoring or signing is connected. Public JSON is allowlisted and
unsigned. Zynth remains deferred; Hack2skill clarification remains pending. No publication,
visibility/licensing, cloud activation or deployment authorization is implied.

## Implemented changes

| Area | Change |
|---|---|
| Shared shell | Navy surfaces, blue primary actions/cyan inspection, contextual breadcrumbs, concise expandable demo notice, labelled commands and connection readiness |
| Gallery | Actual local-state counts act as filters; grid/list views; next action follows review state; compact visible badges; five-column maximum retained |
| Creation | Associated field hints, explicit save-version action, draft/committed distinction, inline fixture evidence and factual upload availability |
| Analysis | Findings take priority after completion; expandable original source; pointer comparison plus native keyboard slider; selected-reference state; inline unrelated-control evidence |
| Review | Blockers/recovery beside decisions; visual/focus order aligned; note assistance beside the note; supplied assertions do not carry verification checks |
| Campaign | Recipient decision follows scope; eligibility remains separate; demo party/time controls grouped; exact-scope revocation confirmation; accepted state replaces repeated acceptance |
| Public preview | Explicit public/private selection; inspect allowlisted export fields; unsigned download; verification requirements are details, not a redundant primary action |
| Drawers | Navigable guide sources, relevant question ordering, filterable/expandable real activity, focused command search/arrow navigation and accurate empty states |
| Responsive/accessibility | Readable metadata, coarse-pointer targets, workspace-container columns, wrapping footer, short-viewport document scrolling, inert skip link and disclosure-aware focus trap |

Historical field snapshots do not exist, so full version comparison remains deferred rather
than fabricated. Drawer activity stays bounded/tab-local. Preview audience controls change
presentation only. Pointer tests use synthetic geometry, not real browser/hardware evidence.

## Validation

The original 73 tests remain covered. The expanded suite currently passes 85 tests across
eight files, including filters/views, navigation, source links, disclosure focus, pointer
clamping, cancellation/confirmation of revocation, accepted states and export privacy.
Final zero-warning lint, Prettier, strict types and production build pass. Shared client JS
remains 166.4 kB gzip against the 250 kB budget. Source functions remain within 50 lines;
changed source/document files remain within the 400-line cap. `git diff --check` is clean.

Frontend fingerprint: `07828ed9eb51ba78499db5cb1700e6d1577e8961d9d66c9440da703108a600c3`
across 60 inputs. Backend fingerprint is unchanged:
`7a50df9ccefa699e26d24ce4302729f332d95f3a1166666f4bba8906b4c1c082` across 120 inputs.
The backend still matches owner validation of 349 tests/96% application coverage; those
database tests were not rerun in the agent sandbox.

Fresh `make check` passed preflight, 776 guard tests (18 skipped), policy, harness and backend
Ruff/Black/Mypy/Bandit, then failed at pip-audit bootstrap (`Failed to upgrade pip`).
Fresh `make frontend` passed lint/format/types and stopped at npm audit registry DNS failure.
Separate passing tests/build/bundle checks do not bypass or complete these audit gates.
No full-green gate or revision-bound CI claim is made. Use the existing repeat commands in
[console review](h1-console-review.md); expect 85 frontend tests and matching current hashes.

## Visual acceptance still required

The existing source server uses [loopback 18664](http://127.0.0.1:18664/); 18660 is the
separate Docker image and may be older. Browser automation failed before session creation
with a sandbox initialization error. No fallback outside that boundary was attempted.
Source/DOM tests do not certify spacing, actual CSS geometry, WCAG or browser interactions.

Review desktop/tablet/320px/390px, both sidebar states, five-column reflow and list mode;
all screens and drawers; short viewports; 200%/400% zoom; touch including wide touchscreens;
keyboard ordering, Escape/focus return and collapsed disclosures; reduced motion; empty,
long-content, blocked, interrupted and completed states. Confirm footer/header never obscure
content and the comparison remains usable with touch and keyboard. Owner visual feedback
precedes expanding beyond this frontend slice.
