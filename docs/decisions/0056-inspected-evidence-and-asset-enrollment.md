# ADR-0056 — Inspected evidence and explicit production asset enrollment

- **Status:** Accepted for source implementation; live activation pending owner acceptance.
- **Date:** 2026-10-05
- **Context:** Owner approved the recommended remaining-MVP order: evidence intake, production
  assets, public passport and issuance records. Inspection must not silently confer production
  rights or public visibility.

## Decision

Reuse encrypted quarantine and exact-version owner authorization. Expose bounded PNG/JPEG/text
upload, inspection, private download, readiness and an injected retention-gate purge through
session-protected routes and matching frontend actions. Image inspection reuses isolated
Pillow/clamd; text requires UTF-8 and clamd. Fail closed on missing providers, unsafe bytes,
digest/type/length mismatch, expiry or permission loss. File choice is local; uploads and
inspection are explicit, same-intent retries.

Enroll clean unexpired retained evidence separately, under an explicit creator permission
statement. The server derives the asset digest; immutable provenance joins exact evidence,
version, owner and request. Limit the existing catalogue to 20 assets per version. Inspection
is not a rights finding. No automatic promotion, reviewer plaintext sharing or public evidence.

Migration 0016 and runtime grants are prepared, not executed. Existing seven-day access expiry
is not physical deletion. Purge requires trusted retention/hold authority, absent by default.
No automatic cleanup claim or permission policy change is made.

## Consequences

New private bytes never enter localStorage, signed public projections or telemetry metadata.
Committed upload/enrollment replay binds the original intent; ambiguous outcomes need manual
retry. Actual SQL/RLS, scanner/Linux/KMS, retention authority and browser acceptance remain
separate gates. See [S8–S10 record](../hackathon/evidence-assets-public-passport-slices.md).
