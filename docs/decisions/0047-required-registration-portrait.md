# ADR-0047: Required registration portrait

**Date:** 2026-10-05
**Status:** Accepted; owner explicitly required a portrait for the AI human-face registry.
**Deciders:** Repository owner

## Context

The earlier persona workflow allowed text-only records. The owner clarified that System Capture
registers an AI persona's face and approved requiring an image. Scan remains an explicit action;
choosing a file must never begin ingestion automatically.

## Decision

New System Capture registrations require a successful inspected portrait attachment, valid text
and explicit save confirmation. Replace optional with required; missing, invalid, pending,
failed, cancelled or discarded selections cannot enable initial saving. Scan uploads and stages
the photo; Save binds it to the immutable version. Local file previews never establish inspection.

Enforce the initial registration rule in the actual HTTP VersionSaveIntent as well as the UI.
New persona intents must attach an upload ID. Existing transactional binding then requires an
authorized owner upload, unexpired staging and both stored payloads. The client cannot send its
own scan verdict. There is no disabled-provider exemption or text-only registration fallback.

Existing records and immutable history remain readable. Existing-version edits keep their wire
contracts, including keeping or explicitly removing an image; an image-free version is incomplete.
The internal persistence contract remains compatible with historical records and fixtures; the
public initial registration boundary applies the new requirement. Historical initial intents
without an attachment are rejected at that boundary; uncertain requests remain exact, never
silently rewritten to add an image or create another record.

Records and version details show Incomplete — portrait required only after an authorized
thumbnail read confirms no attachment. Loading, absent providers and failed reads are separate
unknown/unavailable states, never evidence that a portrait is missing. Key the status to the
workspace/session/version and discard late results; release private preview URLs on cleanup.

This requires an image intended to represent the AI persona's face; no automatic face classifier
or identity/likeness verdict is introduced. Malware inspection and persona analysis remain distinct.

## Activation and consequences

No provider, secret, package, schema/grant, runtime restart or data backfill is authorized here.
Photo service activation still requires the bounded Linux worker, durable scanner/key services,
reviewed migration/grants and real acceptance. New registrations remain blocked until inspection
works. The owner must not restart the connected backend before those schema/grant prerequisites.

Synthetic UI and ASGI tests prove the new requirement and state isolation; PostgreSQL tests prove
durable binding and rollback when run by owner/CI. Neither proves a live scan or rendered geometry.
