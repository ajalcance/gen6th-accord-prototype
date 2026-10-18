# ADR-0042: Records presentation and editing

**Date:** 2026-10-04
**Status:** Accepted for implementation by the owner; photo implementation remains pending.
**Deciders:** Repository owner

## Context

The owner has signed in through Zynth and created a real persona. The Records screenshot
shows repeated search glyphs, inconsistent control heights and a large sparse card. Reopening
a record does not provide an obvious edit action, and the previous editor starts empty. The
owner also requested optional photos during creation and later add/replace/remove editing,
then authorized all recommended improvements before independent reviewer testing.

## Decision

1. Put Create persona in the Records toolbar. Retain global guide/session/command actions.
   Use one integrated search submit action, real Refresh glyph, equal-height Grid/List/Refresh
   controls, and inline count with singular/plural and truthful pagination qualification.
   Keep mobile/coarse-pointer controls at least 44 CSS pixels. Search remains explicit;
   typing or switching display never silently submits a query.
2. Present compact responsive cards using the actual name, biography excerpt, revision and
   saved date, a small unsigned state and visible Open record action. Do not invent a portrait,
   review outcome or campaign permission. Keep grid and list views, accessible button names,
   keyboard focus and narrow-width wrapping. Cards continue to load the selected real record.
3. Expose Edit persona directly. Initialize the existing immutable-version editor with the
   authorized current snapshot when no authored draft exists. Existing workspace/session
   drafts and exact uncertain intents take precedence. Never persist fetched content merely
   because the form opened. Confirmation is still explicit and resets after navigation/edits;
   saving creates a new version and backend membership/ownership remains authoritative.
   Display Record ID in the expanded storage receipt beside Version ID and attribution.
4. Optional photos are part of the authorized work, not an implemented capability yet.
   Prepare a genuine server-inspected, encrypted, version-bound portrait path and create/edit
   controls with saved thumbnails. Changes must create new versions and preserve earlier
   history. The existing seven-day owner-only private evidence quarantine is not a permanent
   persona portrait store or a workspace-sharing grant. Detailed work and outstanding
   installation/runtime prerequisites are in the linked implementation record.

## Consequences and validation

The application keeps the existing services, typed gateway, source/session cleanup and
idempotent save behavior. No permission changes, migration, credential read, server restart,
external service activation, deployment or cleanup accompanies this presentation change.
Regression tests cover explicit search, placement, actual card data, prefilled editing, draft
isolation, confirmation and Record ID. Static build/tests do not certify browser geometry,
zoom or touch behavior; owner rendered acceptance remains required.

[Implementation and photo prerequisites](../hackathon/records-and-photo-implementation.md).

## Alternatives considered

A wide sparse card retains unnecessary space. A second search button repeats the field action.
Resetting saved text on edit increases errors; replacing a local draft loses work. A browser-only
photo preview or a static upload field would imply a saved capability that does not exist.
