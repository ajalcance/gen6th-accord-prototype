# ADR-0059: Performer workspace navigation and progressive capture

Date: 2026-10-06
Status: Accepted for owner-approved frontend implementation

## Context

The owner reviewed Records and System Capture screenshots and approved a comprehensive
workspace redesign. Searches beneath an unbounded-looking gallery hid essential entry points;
large static forms and placeholder journey pages obscured existing backend capabilities.
The owner subsequently requested replacing the wide capture progress panel with a compact helper.

## Decision

Keep name search and a single expandable image-search entry in the Records toolbar. Distinguish
identical file bytes from prepared face similarity. Preserve the submitted query, cursor stack
and grid/list preference during record inspection. Page controls appear above and below results;
counts describe the loaded page, never an invented workspace total.

Use saved-performer context across Analysis & review, Production & use and Passports. Bind the
loaded revision when leaving a record, and provide explicit version selection/current reload.
Without context, offer an authorized, searchable performer picker. Session changes clear selection
and fetched data. Existing in-memory authored drafts and uncertain write intents retain their
session/version keys. Direct write surfaces retain workspace checks and server authorization.

Capture initially expands the persona name, keeps the portrait visible and collapses the other
required declarations. An on-demand Capture helper tracks valid details, scan and confirmation,
opens/focuses the relevant field and explains next steps. It never scans, saves or generates claims.
The explicit Choose → Scan → confirmed registration boundary remains; face processing continues
on the saved version and approved references. Dimensions and provenance are read-only observations.
Use one persistent visible label per field, placing short entry guidance in placeholders. Keep
validation and consequential confirmation text visible. Register persona explicitly approves the
first portrait reference; the adjacent helper replaces repeated footer instructions.

Separate production scope, current permission and recipient decisions. Select up to eight scoped
consent/claim evidence references from metadata, keeping optionality and existing wire semantics.
Separate private passport issuance, public field approval/recipient preview and package verification.
Place Settings and Help in sidebar utilities. Settings contains capability configuration, local
recognition evidence inspection and tab-only presentation preferences; account actions stay in the
header. An available connection is not measured recognition or accepted infrastructure.

## Consequences

Reuse the existing HTTP contracts, mutations, cancellation, exact-retry and access-loss behavior.
No schema, package, provider, key, deployment, guard, telemetry action or authorization policy changes.
Local navigation/helper/copy operations do not assert server audit facts. Existing server actions
retain their telemetry/detection/audit/compliance decisions. Historical activity browsing explicitly
labels its selected historical version. Global queues, counts and cross-workspace timelines need
future reviewed APIs; do not infer them from the loaded page.

Source/DOM and isolated synthetic ASGI tests cover interactions and authorization recovery;
rendered geometry, zoom, touch, real reviewer journeys, recognition measurement and Google/runtime
acceptance remain separate. See [implementation and validation](../hackathon/workspace-redesign-2026-10-06.md).
Later owner screenshots prompted a [cross-page layout audit](../hackathon/workspace-layout-audit-2026-10-06.md):
shared compact states and review-request history in its intended tab implement this same separation.
