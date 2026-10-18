# Records workspace layout review — 2026-10-04

**Implemented for review, ADR-0039.** Owner supplied the October 4 07:17 screenshot and
requested layout/copy changes, then chose an empty workspace gallery until real records
connect, with no sample workflows. Follow-up screenshots at 07:37 and 07:44 required a
denser layout: actions in the header, passport text in FAQ and no repeated page/status labels.
The renewed window is **07:14:45–09:14:45 Manila**.
Provider preparation is deferred while completing this explicitly requested UI slice.

## Element review and implemented placement

| Screenshot element / issue | Revised default view |
| --- | --- |
| Connection & readiness summary, sidebar connection entries and footer Monitoring repeat the same destination | Keep Monitoring in the persistent footer; remove other default readiness triggers |
| Fictional personas / Needs review / Demo reviews and explanatory panels occupy space without real status | Remove the whole summary strip and static Pending review panel; actual review history stays record-bound |
| What does a passport record? is help content | Put it under Frequently asked questions inside Workspace guide |
| Search stayed tall because a more-specific old input selector won | Correct the compact selector; 200px desktop width, 34px-class search/display controls and 44px touch targets |
| Actions, guide and creation are split from navigation and outlined/filled boxes add visual weight | One transparent, borderless action group in the header, matching footer restraint; Cmd/Ctrl K and visible focus remain |
| Browser fixtures / Saved records requires choosing a sample source | Single Records workspace; no sample-source switch |
| Banner and header session status repeat readiness | Remove both; retain Monitoring in the footer and one factual gallery connection prerequisite |
| Gallery breadcrumb, Persona gallery, subtitle and Workspace records repeat context | Header names Persona Passport only; one Records title beside search/display; no subtitle/source label |
| Owner requests Record for singular and Records for plural throughout the UI | Update navigation, titles, commands, return links and accessible labels, including historical test setup; internal query identifiers stay compatible |
| North Studio, fictional avatar and seeded portrait cards imply a populated workspace | Neutral workspace identity until a source is supplied; no seeded records or portraits |
| Creation and navigation can run sample analysis/reviews/campaigns | Creation visibly unavailable; other screens direct to saved records until actual services exist |
| Evidence/activity utilities open unrelated examples | Inspect record-bound governance from the selected saved persona, reusing the existing read workflow |

The supplied screenshots are owner-rendered evidence of the preceding layouts. New source/DOM
tests are not rendered acceptance. The 200px/34px values are authored CSS, not browser measurements.
On narrow containers controls wrap and touch targets remain at least 44px.

## Scope and implementation

`workspace-console.tsx`, `workspace-panel.tsx`, `gallery-display.tsx` and
`workspace-layout.css` implement the default shell. `studio.tsx` preserves the existing saved
source and in-memory write-draft providers. `SavedGallery` adds Grid/List display and factual
empty copy while reusing existing validated queries, cancellation, access-loss cleanup and
record details. New code changes no server data or authorization contract.

Historical seeded workflows are retained only through explicit component `initialState`
injection in tests. `app/page.tsx` passes no initial state or saved source. Old browser storage
is neither loaded into the default workspace nor deleted. Prepared server actions still have
their original internal fixture-only contracts; this UI change does not authorize real uploads,
save real personas, connect trusted sessions or certify app completion.

## Validation record

- Final revised frontend: **257 tests pass** in 9.69s; Node **22.23.1** lint, TypeScript,
  formatting and production build pass. Shared client bundle is **166.4 kB gzip / 250 kB budget**.
  Four new default-layout tests cover samples/storage, grouped controls, guide/FAQ/keyboard
  behavior and supplied-record Grid/List without extra fetching. Twenty-two authored functions
  in the new console/panel and revised gallery are within 50 lines; changed files meet 400 lines.
- **14 ASGI bridge tests pass** in 17.48s; these prove serialization/fault behavior using isolated backend
  test seams, not a trusted live session or authenticated rendered journey.
- `make frontend` passes lint/format/types, then stops at npm audit: `ENOTFOUND registry.npmjs.org`.
  Tests/build/bundle were run separately; audit success is not inferred from those checks.
- Initial `make check` used the shell's Node 23 and failed preflight. Selecting the already
  installed Node 22 fixes that environment error. The Node 22 attempt passes **776 guards /
  18 skips (51.75s)**, policy/harness and backend static/security checks, then stops at
  `pip-audit`: `Failed to upgrade pip`. No guard, audit or sandbox was changed/bypassed.
  Repository-wide SQL/Trust/later frontend/docs gates were not reached by that attempt.
- `make dod-check`, standards/readiness checks and `git diff --check` pass. Browser geometry,
  zoom and touch remain owner acceptance; screenshots do not establish connected services.
- Prior owner full local/14-test ASGI evidence remains a historical frontend checkpoint once
  frontend bytes change. Backend and remediation inputs remain unchanged; do not repeat owner
  SQL solely for this UI slice. Current frontend and PR CI still need matching gate evidence.

```text
backend_source_sha256=375e3d8a776d68b7d77ef01477ef46eef4ada0335bffdfc1179bc89f35e1c5b2 files=159
frontend_source_sha256=30cdecdf0feea7b0aac20fed0f328d50e8979e74b6d8af413f450f4abd5b870c files=137
braces_remediation_sha256=31ff34da5e3cf44786fa2b209ab7c86fce52cf22458c64a03df34cc1250acbdc files=24
```

## Owner visual acceptance

Use the source preview on [127.0.0.1:18664](http://127.0.0.1:18664), after checking its listener.
Refresh Records and confirm the empty layout, transparent header actions, single title/tool
row, compact search/display controls, guide FAQ and sole footer Monitoring entry. Check desktop,
200% zoom, narrow viewport, keyboard focus and touch-sized controls. No terminal command is
needed for this review. Browser automation previously failed at sandbox initialization;
never bypass that boundary or claim rendered acceptance from DOM assertions.

Next implementation is trusted saved-record/creation readiness under a separately reviewed
scope, not restoring the removed sample journey. Evidence-provider research and PR/security
readiness remain open independent tracks.
