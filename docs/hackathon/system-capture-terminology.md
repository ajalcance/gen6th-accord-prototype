# System Capture terminology — October 5, 2026

The owner requested Creation become System Capture in the sidebar and throughout the app.
ADR-0046 records the terminology decision. This changes presentation, not capture capabilities.

Updated surfaces: sidebar label/title/accessibility, Quick Actions destination and navigation,
Records entry button, page heading, form/region labels, workspace guide, save confirmation,
initial save action, success/already-saved messages, receipt/draft labels and restart action.
Use System Capture for the page, Start System Capture for entry, Save System Capture for initial
save and Start another System Capture for restart. Legacy UI fixtures and their test selectors
use the same names. The README and current planning/as-built documents record the new term;
historical decisions and dated evidence keep their original wording.

Persona DTOs, API routes, operation names, database IDs, session-scoped draft keys, exact retry
intent and internal module/style identifiers remain compatible. No migrations, providers,
package installs, runtime configuration or live service changes are included.

Validation: all 281 frontend unit tests pass, including navigation, prefilled editing, retained
drafts, completion replacement/focus, exact uncertain retry and receipt contracts. Lint, format,
strict TypeScript and production build pass. A syntax-aware scan finds zero old display terms
in frontend/app and frontend/lib. Browser geometry remains owner acceptance; the updated labels
may require checking narrow control wrapping. All 15 isolated ASGI integration tests pass and
the shared client bundle remains 166.4 kB gzip against its 250-kB budget. Documentation checks pass.
The fresh full-gate attempt passes 776 guards (18 skipped), policy/harness and backend static
checks, then stops at pip-audit's temporary pip upgrade. The owner's prior full-gate success
certifies the previous fingerprint; it is not claimed as a new full-gate pass for this rename.
No check was bypassed, weakened or removed.

## Explicit Scan action — October 5, 2026

The owner requested a Scan button to begin ingestion instead of automatic scanning. The existing
photo state already separates local selection from an explicit upload. Rename that action Scan,
make it prominent below the portrait picker, describe upload/safety checks, and show Scanning,
Scan complete and Retry scan states. Save still requires a checked photo and explicit confirmation.
The shared editor uses the same labels when replacing a photo. Preview does not ingest bytes;
Scan stages inspected encrypted storage and Save binds it to the version (ADR-0044).
No new action, provider, permission, schema, package or runtime activation is introduced.
Regression coverage asserts selection/confirmation do not upload, pending scans block saving,
and exact retry, cancellation, access loss and workspace receipt validation remain enforced.

Validation for the Scan update: 281 frontend unit tests pass; lint, formatting, strict TypeScript,
production build, bundle budget (166.4 kB / 250 kB) and documentation checks pass. Full `make check`
with the required installed Node 22 passes 776 guards (18 skipped), policy/harness and backend
static checks, then stops at pip-audit's temporary pip upgrade. Later full-gate stages did not run.
Rendered browser acceptance and real-service scanning remain pending; no check was weakened.
