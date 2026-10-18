# Required registration portrait — October 5, 2026

Owner clarified that System Capture is an AI human-face registry and approved a mandatory image.
ADR-0047 records the rule: choose a portrait, explicitly Scan, then save the inspected attachment
with valid declarations and confirmation. Selection/invalid/discarded/failed/cancelled photos
cannot enable initial saving, even with a connected text-writing workspace.

System Capture uses required copy and gates the actual submit handler on an attach receipt.
The actual initial HTTP intent also requires attach; binding authorizes the durable upload owner,
checks expiry and both stored payloads in the version transaction. No browser verdict is trusted.
Historical persistence/wire contracts and existing-version edits remain compatible. Readable
image-free historical versions show Incomplete — portrait required on confirmed authorized
absence. Missing providers, failed reads and loading are separate states. The shared
use-saved-portrait hook keys results to workspace/session/version and ignores cancelled reads.

No services were activated or restarted, packages installed, private configuration accessed,
or real-store schema/grants/records changed. The running backend remains its earlier source.
Image inspection still needs bounded Linux decoding, scanner/key services, migration/grants
and live acceptance. New registrations remain blocked until that work is complete.
This does not activate face detection, likeness analysis, AI review, signing or publication.

Regression scope: missing portrait cannot submit even with valid text/confirmation; choosing
an image does not upload; Scan/retry/save preserve the exact attachment; discarding blocks
initial save; missing/unavailable/late-session results are distinct. Initial HTTP omission,
keep/remove and browser assertions reject; a valid attachment shape passes actual ASGI routes.
SQL tests exercise durable initial binding, exact replay and unknown/other-owner rollback.

Validation: 287 frontend unit tests, all 15 isolated ASGI integration tests and 60 focused
backend contract/HTTP tests pass. The initial-save integration fixture now explicitly selects
and scans a synthetic portrait; authenticated-write/no-client-identity assertions are preserved
and attachment intent is asserted. Lint, formatting, strict TypeScript, production build and
documentation checks pass; bundle remains within 250 kB. Three new SQL cases collect successfully,
but execution requires owner/CI PostgreSQL. No live scanner or browser geometry acceptance is claimed.

Full `make check` passes 776 guard tests (18 skipped), policy/harness and backend static checks,
then stops at pip-audit's temporary pip upgrade failure. Later full-gate stages did not run.
No guard was weakened, suppressed or bypassed; no running service was restarted.
