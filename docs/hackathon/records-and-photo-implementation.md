# Records, Creation and optional portraits — October 4, 2026

## Authorization and implemented UI

The owner approved all recommended Records layout/edit/photo improvements, paused reviewer
testing, requested a focused save result, approved Pillow 12.3.0 installation and then requested
a creative two-column Creation layout. Existing dirty checkout and populated records remain.

- ADR-0042: one integrated search action, equal-height Grid/List/Refresh controls, actual refresh
  glyph, singular-aware count, contextual creation and compact saved cards with real metadata.
  Direct editing prefills authorized saved content while preserving session-scoped authored drafts.
- ADR-0043: confirmed creation replaces the editor, focuses success and collapses storage IDs.
  Open saved record performs a fresh authorized read; retained authored markers prevent duplicate
  creation without restoring fetched receipts. Later text remains explicitly inspectable.
- ADR-0045: compact details on the left and a large uncropped 4:5 portrait panel on the right.
  Below 850px of workspace width, portrait precedes details, matching document/keyboard order.
  A native accessible picker, filename, format/size hints and explicit discard/check actions sit
  beside the image. Confirmation and save/navigation actions follow both columns.
- Local previews work without a photo gateway. Selection alone is unsaved, never uploads and
  blocks submission until checked or discarded. Invalid selection/discard preserves text;
  preview URLs are revoked on replacement, completion and screen/session cleanup.

## Prepared portrait source; runtime activation remains pending

ADR-0044 prepares optional checked upload, exact retry/cancellation, private saved thumbnails
and immutable add/keep/replace/remove version bindings. Server intake authorizes the current
creator before bounded bytes, validates digest/length/type/replay, scans original and derivative,
fully decodes within a bounded child worker and generates a metadata-free PNG. Per-object
AES-GCM ciphertext and context-wrapped keys live in separate PostgreSQL tables. Only authorized
thumbnail reads exist; no original browser route or public URL is accepted.

Pillow 12.3.0 is installed and direct synthetic PNG/JPEG pixel tests pass. The Mac child cannot
establish required memory limits and explicitly reports unavailable; limits were retained.
Photo activation requires a verified bounded Linux runtime. Clamd requires current definitions
and exact inspection results; Vault Transit requires an existing derived non-exportable key and
scoped token. Neither service is installed or active. Owner-only preparation includes additive
migration 0010portraits, runtime SELECT/INSERT grants and narrow Vault policy. No schema, grant,
key, configuration or running service was changed.

**Do not restart the connected backend on this changed source before schema/grant review.**
Existing-version writes now read the portrait-binding table even with photo intake disabled.
Migration 0010 and confined runtime grants must be verified first against the populated store.
No real-store migration is part of the test command below.

Staged attachments expire after 24 hours; expiry is not deletion authority. Immutable payloads
and historical bindings remain. Trusted retention/legal-hold rules and a bounded cleanup worker
are unfinished; no purge or DELETE grant is active. Runtime provider installation still requires
the owner's per-install approval under AGENTS.md. Pillow approval need not be repeated.

## Evidence and remaining acceptance

**Latest owner result:** full `make check` reports `photo_check_exit_status=0` on October 4.
Reported after fingerprint is `7b422e4a907feb92b1f98ba366e78a0ec1f8e991a138dbdbae4596204a07ace9`,
473 public source files; agent recomputation matched before this documentation-only record update.
The output reaches frontend production build/budget and docs-site lint/format/audit, 31 tests
and build. The Makefile's complete check target includes backend PostgreSQL, Trust and frontend
checks; its zero result closes the earlier two-failure full-gate prerequisite for this source.
The supplied tail does not include new backend test counts or coverage; do not invent them.
This is owner-run evidence, not an agent Docker execution or real photo acceptance.

Owner reports Zynth onboarding, confidential-client registration, private mode-600 local config,
database/Redis probes, distinct creator/reviewer bindings, real sign-in and first persona save.
The earlier empty-store inventory is historical. The real record is Gen6th Female Model,
version <record-version-id>. These are owner reports, not agent reads of secrets
or private database content. Independent reviewer and reload/read-back proof remain pending.

Current source validation: 281 frontend unit tests pass, including disconnected preview,
invalid selection, exact upload retry, cancellation, session isolation, attachment and removal.
Lint, format, TypeScript, production build and the 166.4-kB client budget pass; 15 isolated ASGI
integration tests pass. Documentation checks pass. Owner rendered acceptance remains open.
Owner then ran the full gate: 776 guards pass (18 skipped), backend static checks and dependency
audit pass, followed by 637 backend tests passing and two failing with 92.32% coverage. Trust,
frontend and later full-gate steps were not reached. Owner's reported after fingerprint matches
the pre-fix checkout: 2ce4ac6e27bac7bf7d8145ea4403e334f5a05c52be3badd3ba042e59716d3666, 472 files.
The beginning fingerprint line in the pasted output was truncated; full before/after equality
is not independently asserted from that output.

The migration check correctly exposed payloads outside its persona table population. Fix the
unapplied source/model/grant preparation to use `persona_portrait_payloads` and the shared
`immutable_record` trigger; preserve the migration test unchanged. Offline schema protection
rendering passes. No populated runtime schema or existing service was modified.
The earlier exact detection inventory test expected only pre-portrait actions. The four-line
extension adds uploaded/inspected/bound/read while preserving equality and unknown/client
exclusions. AGENTS.md required owner approval before changing the blocked check; the owner
explicitly approved the prepared four-line patch and it is now applied.
Four new SQL regression cases exercise durable portrait detection, client-source rejection,
tenant-isolated findings and replay. Ten portrait SQL tests collect; they are not SQL-executed
in the agent sandbox. Post-fix isolated tests pass (62), including the unchanged offline migration
protection check and approved exact action inventory. Lint, format, strict types and documentation
checks pass. The agent's backend runner stopped at pip-audit bootstrap; the later owner full
gate result above supplies post-fix SQL/full-gate proof. Runtime prerequisites remain open.

Source/DOM tests do not certify rendered geometry. Owner browser acceptance must cover desktop
and narrow layouts, long text/filenames, keyboard/native picker, zoom/touch, success focus and
draft retention. Photo runtime acceptance additionally needs real Linux decoder, clamd/Vault,
tenant/owner isolation, provider faults, immutable history and restart/decryption recovery.

## Owner Mac full-gate verification

Completed successfully for the fingerprint above. Retain this command for future code changes;
the following evidence-record update changes only documentation and receives documentation checks.

Run only against the current public source. This uses disposable test databases, does not apply
real-store migrations, enable photo providers or read private config through the fingerprint.
Existing Docker availability is required. Report the two fingerprint lines and exit status;
matching fingerprints plus exit zero establish the checked source, not browser acceptance.

```sh
(
  cd "/path/to/gen6th-accord" || exit
  shasum -a 256 -c <<'SHA'
a188bc6fa30fc675e739acc16d64e9e30f9e0d8c5ca074ab6fed74b1f4a3d31d  .cache/photo-processing/review_fingerprint.py
SHA
  integrity_result=$?
  if [ "$integrity_result" -ne 0 ]; then exit "$integrity_result"; fi
  photo_source_before=$(backend/.venv/bin/python .cache/photo-processing/review_fingerprint.py) || exit
  printf 'photo_source_before=%s\n' "$photo_source_before"
  env PATH="/opt/homebrew/opt/node@22/bin:$PATH" make check
  photo_gate_result=$?
  photo_source_after=$(backend/.venv/bin/python .cache/photo-processing/review_fingerprint.py) || exit
  printf 'photo_source_after=%s\n' "$photo_source_after"
  printf 'photo_check_exit_status=%s\n' "$photo_gate_result"
  if [ "$photo_source_before" != "$photo_source_after" ]; then exit 1; fi
  exit "$photo_gate_result"
)
```
