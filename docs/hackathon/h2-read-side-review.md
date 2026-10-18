# Read-side connection preparation — 2026-10-02

This checkpoint precedes [session/read preparation](h2-session-read-review.md); its 421-test
result applies only to the source fingerprint recorded here.

The owner authorized continued building after the 397-test/96.35% checkpoint. This slice
implements the remaining gallery/history/evidence read contracts (ADR-0033). The renewed
validation window remains **18:02:25–20:02:25 Asia/Manila**; it was not reset.

## Implemented

- Workspace-authorized gallery of current versions, default 20/max 100, stable UUID cursor,
  escaped literal search, and a server observation even for an empty result. No global totals.
- Owner-only private evidence status without decryption, bytes, key handles or storage URLs.
  Status reads identify themselves as metadata observations in the existing audit action.
- Disconnected frontend read adapters for gallery, review/campaign history, private evidence
  status and workflow audit references. They reject wrong tenants/records, duplicates,
  incorrect ordering, oversized pages, invalid cursors and incomplete audit references.
- Shared fictional read examples validated by the actual backend models. Cancellation
  discards late results even when the injected transport ignores the abort signal.

No UI connection, identity fallback, scanner/key/retention provider, cloud activation,
signing, publication or persistent-database migration. The console remains labelled fixtures.
Prepared read adapters do not create an authenticated browser-to-backend journey.

## Verification

Owner PostgreSQL run: **421 tests pass in 71.00s**, **96.42% application coverage**
(1,982 statements, 71 missed; required floor 70%). The supplied output contains the trailing
fingerprint, matching the requested precondition and the agent's independent current-source
rehash. The leading output was not included in this excerpt.

- Backend SHA-256: `1f4a1a240e173c11a3e7b15bd9424d05db8ce0126c69a66ab8a474779d3f8a0a`
  across **141 inputs**, including the shared wire fixture.
- Frontend SHA-256: `19d1dda7f6ebe533436720a97d036e65902036967fca32a9fc3878c3ab7685f3`
  across **75 inputs**, including the shared wire fixture.
- **128 frontend tests / 11 files** and **64 targeted backend checks** pass. Backend
  ruff/black/mypy/Bandit and frontend lint/format/types/production build pass.
  Shared client bundle: **166.4 kB gzip / 250 kB budget**.
- Full gate passes 776 guards / 18 skips and policy/harness/backend static checks, then
  stops at pip-audit bootstrap. Frontend audit stops at registry DNS. These remain open;
  no full-green gate, authenticated HTTP journey or new browser acceptance is claimed.

The earlier 397-test checkpoint remains evidence for the preceding source only.

## Review units and next dependencies

Keep the gallery/status service, frontend read contracts, and shared-doc hunks reviewable
separately from the earlier evidence, UI and policy work. No staging, commit or PR was made.
Next dependencies: full audits, approved trusted sessions and
the real decoder/scanner/key/retention providers. UI loading/paging integration follows those
contracts and must not turn browser role selectors into authorization.
