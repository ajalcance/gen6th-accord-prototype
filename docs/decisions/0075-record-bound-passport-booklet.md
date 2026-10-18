# ADR-0075: Record-bound paper passport booklet

- Status: Accepted for source preparation; owner approved the paper design on 2026-10-17
- Date: 2026-10-17
- Extends: ADR-0054 integrity, ADR-0057 private issuance and public sharing, ADR-0059 navigation

## Context

The owner approved two facing patterned paper pages with the original Accord logo, navy serif
headings, an approved portrait, record fields and a signed-record panel. The supplied reference's
black background and leather case are excluded. The booklet must show actual saved records,
including performers without an offer or an approved portrait, without inventing issuance.

## Decision

1. Place View passport above production offers; enable after authorized scope discovery. Open a native modal dialog with a close control,
   restored focus, responsive stacked pages and print rules. Draw text and ornaments in HTML/SVG;
   reuse system fonts, the original vector logo and native security pattern. No example portrait
   or fictional field values enter the product. Portraits use approved-reference authorization.
2. Reuse capture query/thumbnail, campaign status, package verification and publication history.
   Add no route, backend action, database shape or storage. Opening never exports or approves.
   Read share history only after valid private package verification because history is owner-only.
   Inspect up to ten existing history pages per refresh; unavailable records keep the preview.
3. A registered preview has a dashed unsigned panel and no seal or QR. An issued display requires
   an exact version/offer-bound private package, valid server verification, a nonwithdrawn approved
   public receipt bound to the saved revision/name/disclosure/dates, and successful local QR
   encoding of its same-origin approved URL. Browser parsing alone is not verification. A private
   share receipt does not establish anonymous public availability; the view says so.
4. Retain a private package only after the existing explicit Prepare signed passport action.
   Abort checks reject late completions. Workspace/session/version remounts and offer/page changes
   clear it. Switching private/public/verification controls preserves it within that scope.
   Reload returns to preview until another explicit preparation; no new private lookup is added.
5. Derive the display reference as AC plus the last eight offer UUID digits. It is a display
   reference, not a unique registry identifier. Without an offer show Not assigned and No
   production offer. Show the actual key-version tail and private payload issue time in UTC;
   never label a key identifier a fingerprint or substitute registration/approval time.
6. Label human contribution and AI disclosure as separate creator statements. Show recorded
   scope as a recorded offer, and current permission separately with evaluation time and a
   refresh control. A signed historical record grants no continuing permission. The machine
   line is Accord-specific and hidden from assistive technology. A visible disclaimer states
   that this is an Accord record, not a government document.

## Consequences and acceptance

The approved appearance can display genuine saved registration records before KMS/public serving
are enabled. Missing/denied/invalid/unavailable states cannot mint a seal or QR. Existing session
loss propagation clears the private view. Blob thumbnails stay in memory and object URLs revoke
on replacement/close. No external fonts, images, model calls or dependencies are added.

The handoff's missing-Node assumption was refreshed: a desktop-bundled Node24.19.0 and existing
dependencies allowed565 frontend tests, TypeScript, lint and an optimized build to pass. Production
Node22 parity, rendering, keyboard behavior, narrow layouts and print remain unverified. Owner/CI acceptance, genuine signing/publication and public
QR browser proof are required before a live claim. The combined demo bundle excludes new booklet
test files as a bounded demo payload; all remain in the local source branch for production Node22 CI.

## Deferred

Public-page booklet rendering, PDF/image export, a stored registry number, a real key fingerprint,
new issuance read routes and public activation require separate work. No scanner, freshness
window, guard, IAM, cloud service, pitch deck, repository publication or release policy changes.
