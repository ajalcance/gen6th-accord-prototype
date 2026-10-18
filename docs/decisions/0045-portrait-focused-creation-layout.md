# ADR-0045: Portrait-focused creation layout

**Date:** 2026-10-04
**Status:** Accepted; owner requested a creative two-column Creation redesign.
**Deciders:** Repository owner

## Context

Creation spread short fields across a wide canvas and placed a small file picker below them.
The persona image received little emphasis. The owner requested details on the left and an
image-focused right column before resuming independent reviewer testing.

## Decision

Use two bounded columns: compact, vertically ordered details on the left and a large portrait
panel on the right. Show the complete selected image in a 4:5 frame without cropping. Before
selection show a neutral outline, not a fabricated persona. Keep optional status, accepted
formats, filename and selection/check/discard controls beside the image. Below both columns
place the existing explicit confirmation and save/navigation actions.

Below 850 pixels of workspace width stack the portrait above details. Put the portrait first
in document order so narrow-screen reading and keyboard order agree. Keep the native file
input keyboard accessible with a visible focus outline and a 44-pixel selection target.
Avoid sticky panels that can hide controls during zoom or short-window use.

Allow local selection and preview even when no photo service is connected. This never uploads
or persists image bytes. An unchecked selection blocks submission; check it with the connected
service or discard it to save text alone. Existing session cleanup, exact retry, late-result
rejection and immutable attachment contracts remain in force. Successful creation still
replaces the editor with ADR-0043's focused confirmation.

## Consequences

Creation emphasizes persona identity while retaining all required disclosure fields. Editing
reuses compact photo controls. Source/DOM tests establish interaction behavior; desktop,
narrow-screen, zoom and native-picker acceptance remain owner browser checks. This layout does
not activate scanner, key services, schema/grants or the photo runtime described in ADR-0044.
