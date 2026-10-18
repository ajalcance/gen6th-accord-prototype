# Retained prototype changelog

- Expose prepared governance concepts in an “Evidence & decisions” panel on all five screens
  (ADR-0035): immutable versions, independent review/decision history, quarantined/rejected/
  expired evidence, pending audit references and unsigned records. Separately labelled local
  contract examples use no network or real writes. Empty/denied/unavailable states, read-only
  conflict comparison and same-intent retry preserve drafts. 192 frontend tests/static checks/
  build/budget pass; current npm audit is blocked by sandbox registry DNS. Backend unchanged.
- Prepare session-gated gallery/version HTTP queries and a separate saved-record view
  (ADR-0034), with search/paging, read-only details and explicit loading/failure recovery.
  Default UI reports missing connection; verifier and routes remain inactive. Clear old
  responses across cancellation/access changes. Zynth remains gated. Owner full `make check`
  passes: 454 backend tests / 96.55% coverage, 151 frontend tests, 11 docs-site tests and audits.
- Add internal authorized current-version gallery pagination and private evidence status,
  plus disconnected frontend history/evidence read contracts (ADR-0033). Literal search,
  tenant/item/cursor validation and metadata-only observations preserve existing boundaries.
  Owner run passes 421 backend tests (96.42% coverage), with a matching current fingerprint;
  frontend passes 132 tests and production build. Full audits and live UI connection remain open.
- Prepare internal encrypted private-evidence quarantine and default-disconnected persona
  transport/recovery (ADRs 0031/0032). Owner installed pinned cryptography 50.0.2. No scanner,
  key/retention provider, trusted session or persona HTTP route is activated. Verification
  and remaining gates are recorded in `docs/hackathon/h2-connection-plan.md`.
  Owner database repeat passes 397 tests with 96.35% application coverage and matching source
  fingerprints; frontend passes 109 tests. Dependency audits and live integration remain pending.
- Fourth-pass persona console (ADR-0030): navy/blue/cyan visual hierarchy, actionable queues,
  grid/list browsing, inline evidence, draggable comparison, explicit blockers, confirmation
  before revocation, grouped unsigned exports, source navigation and keyboard command search.
  Responsive/touch/focus refinements preserve fixture-only boundaries. Validation and outstanding
  browser/full-gate evidence are recorded in `docs/hackathon/h1-fourth-pass-review.md`.

- Refreshed the next-session handoff with current console scope, source-bound validation,
  visual-review priority, preserved review units and unresolved activation/audit gates.

- Second/third-pass local persona console: independent bounded drafts, versions/history,
  cancellable staged scan and actual palette comparison, scripted assistance and command search.
  Campaign offers, recipient decisions, revocation and current eligibility are distinct.
  Compact task headings, collapsible sidebar, container-responsive five-column gallery and
  anchored status footer use semantic tokens. Secondary controls use progressive disclosure;
  monitoring is explicitly disconnected. ADRs 0028/0029; no API/cloud/signing/publication activation.
  73 frontend tests/static checks/build pass; dependency audits and final visual review remain pending.

- Audited frontend/backend alignment: persona UI remains explicitly browser-only. Note edits
  clear stale demo decisions, comparison waits for scenario readiness and provenance correctly
  describes one illustration in three palettes. Changed drafts clear old evidence notes;
  31 frontend tests pass.
  Owner repeat round passed all 349 backend tests; application-only coverage reports 96%.
- Durable internal persona detection: atomic findings/checkpoints, retry/restart recovery,
  late events and scoped backlog observation. Pending windows survive retention; old-window
  uncertainty is explicit. Owner source-bound PostgreSQL validation passed all 301 target
  tests in 50.58s; full gates remain incomplete.

- Corrected campaign expiry boundary test fixtures to share an exact expiry instant;
  owner revalidation passed all 279 target tests with matching source fingerprints.
  Production expiry checks are unchanged; full gates remain incomplete.

- Prepared a controlled matching evaluation protocol with provenance, family-level splits,
  transform strata and explicit denominators. No model integration or benchmark result claimed.

- Internal fictional campaign permissions: immutable owner scope and asset/version/review
  bindings, independent recipient decisions, change requests and final creator revocation.
  Current eligibility and private history/evidence inspection remain separate from historical
  retry receipts. SQL tests passed in the owner-run target; no activation or signing performed.

- Internal fixture review persistence: immutable version-bound decisions, independent reviewer
  checks, self-review denial, optimistic ordering, retry receipts and bounded observed history.
  PostgreSQL tests passed in the owner-run target; no review route or identity integration activated.
