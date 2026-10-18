# Passport booklet source and acceptance — 2026-10-17

The owner approved the paper mock on 2026-10-17. The production components follow its facing
pages, pale security pattern, original logo, navy serif text, portrait watermark and record panel.
The black surround and leather case are removed. No fictional portrait ships in the product.

## Verified locally

- Full frontend selection: **70 files, 566 tests passed** using existing dependencies and the
  desktop-bundled **Node24.19.0**. No installation occurred. The18 new booklet cases cover derived
  references, private/public package binding, issue date/key mapping, invalid verification,
  approved-reference thumbnails, no offer, no portrait, later/withdrawn share history, session
  clearance, refresh clearance, access loss, close/focus restoration and object URL cleanup.
  Existing late-export/offer-change and explicit issuance/publication tests also pass.
- Strict TypeScript, full-project ESLint and changed-file formatting pass. The optimized
  Next16.3.8 webpack build passes; shared client bundle is166.8kB against the unchanged250kB
  budget. Full-project formatting finds two pre-existing reviewer-brief files:
  `app/passport/record-brief.tsx` and `tests/record-brief.test.tsx`. Their upstream formatting
  follow-up remains open; the booklet branch does not silently alter the separate T2 write-set.
- Second-agent manual review found an owner-only share-history read in unsigned previews and
  a focus restoration defect. Both are fixed. Preview does not query owner history; valid private
  verification precedes that read. The launcher is captured before dialog autofocus.
- Existing DoD guard passes: ten top-level directories, eight backend modules, five frontend
  directory roots and77 ADR entries including index/template. Unicode guard inspected1172 files.
- All changed files remain within400 lines; changed product functions remain within50 lines.
  Oversized existing records were split by concern into retained history pages without weakening
  guards or deleting their content. No backend, lockfile, guard or deployment policy is modified.

## Evidence limits

The pinned production runtime is Node22; the available bundled runtime is Node24.19.0. These
tests/build are real local checks but do not establish production parity. Native dialog focus,
keyboard trapping/Escape, responsive layout, print, screen-reader behavior and visual fidelity
still need a real browser. DOM tests are not browser rendering evidence.

Full `make check` stops at the unchanged preflight: the isolated copy has no backend venv or
docs-site dependencies and no Node executable on its default PATH. The frontend commands above
use absolute paths to existing dependencies. Backend/Trust/database tests, audits, production
Node22 CI/container build, genuine KMS issuance, public serving and cloud deployment remain open.
No code or guard was changed to bypass that preflight.

## Required browser and live acceptance

1. View passport waits for authorized scope discovery; an unavailable scope is not absence.
   Open a saved performer on Passports. View passport is above the offer list and works with no
   offer. Check the light surround, paper pattern, actual name and separate creator statements.
   Without an offer show Not assigned / No production offer; do not infer permission or issue time.
2. Try an inspected but unapproved portrait and a performer without a portrait. No inspected
   image is represented as an approved reference. Confirm empty/unavailable wording separately.
3. Check desktop and narrow layouts, long names/disclosures/scopes, 200% zoom, contrast and focus.
   Open/close/Escape must restore View passport. Inspect print output for complete text and pages.
4. Before live signing/public activation, show only preview: no signed seal and no QR. Viewing
   must not export, approve, unpublish or call model services.
5. After separately accepted signing/public serving, explicitly prepare a private package and
   approve selected public fields. Reopen the booklet: actual issue time/key tail and approved
   link must match saved records. Scan the QR in an anonymous browser. Verify public integrity
   and separately evaluated permission. The private receipt alone does not prove public access.
6. Switch private/public controls, then offer/version/session. Retention is allowed only inside
   the same workspace/session/version/offer. Reload returns to preview until explicit preparation.
7. Refresh after withdrawal, expiry, revocation and membership loss. Old seal/QR/portrait clear
   during reads, and denied access clears the private record surface. Check blocked permission
   separately from historical package integrity. No signature proves identity, rights or ownership.
8. Confirm the combined frontend also exposes the advisory reviewer brief and complete that
   feature's real browser proof; G1/G2 owner output does not establish the API service account call.

## Delivery boundary

Source is prepared for `feat/passport-booklet` on the reviewer-brief tip. Git object writing failed
in the protected `.git` directory; the branch does not exist yet. The self-checking local owner
helper completes that step without switching or editing the dirty checkout. No escalation was tried.
The combined archive starts from the accepted Gemini frontend archive and retains its
PR84 Dockerfile/build arguments. Only explicit booklet paths are overlaid. New booklet test files
remain in source for CI and are excluded from the demo image; the image is not the complete gate.
The owner script checks its archive hash/account, builds with the pinned builder, deploys by digest,
checks expected URLs/statuses/assets and prints rollback before mutation. It has not been executed.
No push, pull request, pitch edit, scanner substitute/freshness change or cloud action is included.
